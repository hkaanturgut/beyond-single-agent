"""Fan-in aggregator — combines specialist outputs into a TripProposal."""

from __future__ import annotations

from trip_planner.models.proposal import (
    BudgetOutput,
    PlanOutput,
    ResearchOutput,
    TripProposal,
)
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("workflow.aggregator")


async def aggregate(state: WorkflowState) -> WorkflowState:
    """Merge fan-out outputs into ``state.proposal``.

    Missing specialist results are replaced with empty defaults so the
    workflow never stalls due to a single specialist failure.
    """
    with stage_span(_log, "aggregate"):
        state.proposal = TripProposal(
            request=state.request,
            research=state.research_output or ResearchOutput(),
            itinerary=state.plan_output or PlanOutput(),
            budget=state.budget_output or BudgetOutput(),
        )
    return state
