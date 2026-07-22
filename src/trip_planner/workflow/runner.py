"""Main workflow runner — assembles the pipeline and executes it end-to-end.

This is the single entry-point for actually running a trip-planning session.
The CLI calls ``run_trip_workflow``; tests can also call it directly with
a pre-configured backend.
"""

from __future__ import annotations

from trip_planner.agents.budget import BudgetAgent
from trip_planner.agents.finalizer import FinalizerAgent
from trip_planner.agents.optimizer import OptimizerAgent
from trip_planner.agents.planner import PlannerAgent
from trip_planner.agents.researcher import ResearcherAgent
from trip_planner.backends.base import BackendAdapter
from trip_planner.models import FinalTripBrief
from trip_planner.models.request import TripRequest
from trip_planner.models.validation import ROUTE_OPTIMIZE
from trip_planner.output.writer import write_brief
from trip_planner.workflow.aggregator import aggregate
from trip_planner.workflow.builder import WorkflowBuilder
from trip_planner.workflow.router import route_selector, validate_and_route
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger

_log = get_logger("workflow.runner")


def build_workflow(backend: BackendAdapter) -> object:
    """Construct the trip-planner workflow graph.

    Stage map
    ---------
    1. fan-out: researcher / planner / budget  (ConcurrentBuilder)
    2. aggregate
    3. validate_and_route
    4. route: optimize → OptimizerAgent  |  finalize → FinalizerAgent
       (add_multi_selection_edge_group)
    """
    researcher = ResearcherAgent(backend)
    planner = PlannerAgent(backend)
    budget = BudgetAgent(backend)
    optimizer = OptimizerAgent(backend)
    finalizer = FinalizerAgent(backend)

    workflow = (
        WorkflowBuilder("trip-planner")
        .add_concurrent()
            .add_task("researcher", researcher.run)
            .add_task("planner", planner.run)
            .add_task("budget", budget.run)
        .done()
        .add_step("aggregate", aggregate)
        .add_step("validate_and_route", validate_and_route)
        .add_multi_selection_edge_group(
            "route-to-agent",
            selector=route_selector,
            branches={
                "optimize": _make_optimize_then_finalize(optimizer, finalizer),
                "finalize": finalizer.run,
            },
        )
        .build()
    )
    return workflow


def _make_optimize_then_finalize(
    optimizer: OptimizerAgent, finalizer: FinalizerAgent
):
    """Return a coroutine function that runs optimizer then finalizer."""

    async def _optimize_then_finalize(state: WorkflowState) -> WorkflowState:
        state = await optimizer.run(state)
        state = await finalizer.run(state)
        return state

    return _optimize_then_finalize


async def run_trip_workflow(
    request: TripRequest,
    backend: BackendAdapter,
    output_dir: str = "output",
) -> FinalTripBrief:
    """Run the full trip-planning pipeline and return the final brief.

    Args:
        request:    Validated trip request.
        backend:    Instantiated backend adapter (demo, github_models, or foundry).
        output_dir: Directory to write the markdown output file into.

    Returns:
        :class:`FinalTripBrief` with the markdown content and file path.
    """
    state = WorkflowState(request=request, backend_name=backend.name)
    workflow = build_workflow(backend)

    state = await workflow.run(state)

    if state.final_brief is None:
        _log.error("Workflow completed without producing a final brief; generating stub")
        from trip_planner.agents.finalizer import _render_markdown  # type: ignore[import]
        from trip_planner.models.proposal import TripProposal
        proposal = state.proposal or TripProposal(
            request=request,
        )
        markdown = _render_markdown(proposal, "- Review manually.", None)
        state.final_brief = FinalTripBrief(markdown=markdown, output_path="")

    # Write to disk and patch the output_path
    path = write_brief(
        state.final_brief.markdown,
        destination=request.destination,
        output_dir=output_dir,
    )
    state.final_brief.output_path = path

    if state.errors:
        _log.warning("%d non-fatal error(s) during workflow: %s", len(state.errors), state.errors)

    return state.final_brief
