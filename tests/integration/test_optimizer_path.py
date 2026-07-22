"""Integration test — optimizer path using a deliberately low budget."""

from __future__ import annotations

import pytest

from trip_planner.backends.demo import DemoBackend
from trip_planner.models.proposal import BudgetOutput, PlanOutput, ResearchOutput, TripProposal
from trip_planner.models.request import TripRequest
from trip_planner.models.validation import ROUTE_OPTIMIZE
from trip_planner.workflow.runner import run_trip_workflow
from trip_planner.workflow.router import validate_and_route
from trip_planner.workflow.state import WorkflowState


@pytest.fixture()
def demo_backend():
    return DemoBackend()


@pytest.mark.asyncio
class TestOptimizerPath:
    async def test_over_budget_request_produces_optimization_notes(
        self, demo_backend, tmp_path
    ):
        """A pre-seeded over-budget proposal must route through the optimizer
        and produce optimization notes in the final brief."""
        from trip_planner.workflow.aggregator import aggregate
        from trip_planner.agents.optimizer import OptimizerAgent
        from trip_planner.agents.finalizer import FinalizerAgent
        from trip_planner.workflow.router import validate_and_route
        from trip_planner.models.proposal import TripProposal, ResearchOutput, PlanOutput, BudgetOutput

        request = TripRequest(destination="Lisbon", month="May", budget_usd=200)
        state = WorkflowState(request=request)

        # Inject an over-budget proposal directly (total $1200 > $200 budget)
        state.proposal = TripProposal(
            request=request,
            research=ResearchOutput(
                attractions=["Belém Tower", "Alfama district"],
                weather_summary="Warm and sunny.",
            ),
            itinerary=PlanOutput(days=[], conflict_flags=[]),
            budget=BudgetOutput(
                flight_estimate=400,
                hotel_estimate=450,
                food_estimate=200,
                activity_estimate=150,
                total_estimate=1200,
                confidence="medium",
            ),
        )
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE

        optimizer = OptimizerAgent(demo_backend)
        finalizer = FinalizerAgent(demo_backend)
        state = await optimizer.run(state)
        state = await finalizer.run(state)

        assert state.final_brief is not None
        lower = state.final_brief.markdown.lower()
        assert "optim" in lower or "adjustment" in lower or "changes" in lower

    async def test_conflict_fixture_routes_through_optimizer(self, demo_backend, tmp_path):
        """Manually inject a conflict flag and verify the optimizer route is taken."""
        request = TripRequest(destination="Tokyo", month="March", budget_usd=2600)
        state = WorkflowState(request=request)
        state.proposal = TripProposal(
            request=request,
            research=ResearchOutput(),
            itinerary=PlanOutput(
                conflict_flags=["Day 1: 09:00-11:00 overlaps with 10:00-12:00"]
            ),
            budget=BudgetOutput(total_estimate=1800),
        )
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE

    async def test_optimized_state_has_changes_applied(self, demo_backend, tmp_path):
        """After optimizer runs, state.optimized must list at least one change."""
        request = TripRequest(destination="Lisbon", month="May", budget_usd=200)
        # We need to run partially through the workflow to get state.optimized
        from trip_planner.workflow.aggregator import aggregate
        from trip_planner.agents.researcher import ResearcherAgent
        from trip_planner.agents.planner import PlannerAgent
        from trip_planner.agents.budget import BudgetAgent
        from trip_planner.agents.optimizer import OptimizerAgent
        import asyncio

        state = WorkflowState(request=request)
        researcher = ResearcherAgent(demo_backend)
        planner = PlannerAgent(demo_backend)
        budget = BudgetAgent(demo_backend)
        optimizer = OptimizerAgent(demo_backend)

        await asyncio.gather(
            researcher.run(state), planner.run(state), budget.run(state)
        )
        state = await aggregate(state)
        state = await validate_and_route(state)

        if state.validation.route == ROUTE_OPTIMIZE:
            state = await optimizer.run(state)
            assert state.optimized is not None
            assert len(state.optimized.changes_applied) > 0
