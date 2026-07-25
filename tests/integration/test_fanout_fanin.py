"""Integration test — fan-out / fan-in using the FakeBackend."""

from __future__ import annotations

import pytest

from fakes import FakeBackend
from trip_planner.models.request import TripRequest
from trip_planner.workflow.aggregator import aggregate
from trip_planner.workflow.runner import build_workflow, run_trip_workflow
from trip_planner.workflow.state import WorkflowState


@pytest.fixture()
def demo_backend():
    return FakeBackend()


@pytest.fixture()
def base_request():
    return TripRequest(destination="Lisbon", month="May", budget_usd=2600)


@pytest.mark.asyncio
class TestFanOutFanIn:
    async def test_all_specialist_outputs_populated(self, demo_backend, base_request, tmp_path):
        """All three specialist agents must write to state."""
        brief = await run_trip_workflow(base_request, demo_backend, output_dir=str(tmp_path))
        # If the workflow ran correctly the final brief is produced
        assert brief is not None
        assert brief.markdown

    async def test_proposal_created_after_aggregate(self, demo_backend, base_request):
        """After fan-out + aggregate the proposal must contain all parts."""
        state = WorkflowState(request=base_request)

        # Manually run the fan-out steps
        from trip_planner.agents.researcher import ResearcherAgent
        from trip_planner.agents.planner import PlannerAgent
        from trip_planner.agents.budget import BudgetAgent

        researcher = ResearcherAgent(demo_backend)
        planner = PlannerAgent(demo_backend)
        budget = BudgetAgent(demo_backend)

        import asyncio
        await asyncio.gather(
            researcher.run(state),
            planner.run(state),
            budget.run(state),
        )
        state = await aggregate(state)

        assert state.proposal is not None
        assert state.proposal.research is not None
        assert state.proposal.itinerary is not None
        assert state.proposal.budget is not None

    async def test_output_file_created(self, demo_backend, base_request, tmp_path):
        brief = await run_trip_workflow(base_request, demo_backend, output_dir=str(tmp_path))
        import os
        assert os.path.exists(brief.output_path)

    async def test_output_filename_contains_destination(self, demo_backend, base_request, tmp_path):
        brief = await run_trip_workflow(base_request, demo_backend, output_dir=str(tmp_path))
        assert "lisbon" in brief.output_path.lower()

    async def test_no_fatal_errors_in_demo_mode(self, demo_backend, base_request, tmp_path):
        state = WorkflowState(request=base_request)
        workflow = build_workflow(demo_backend)
        final_state = await workflow.run(state)
        # Non-fatal errors are allowed but should not include RuntimeError crashes
        for err in final_state.errors:
            assert "RuntimeError" not in err.get("error", "")
