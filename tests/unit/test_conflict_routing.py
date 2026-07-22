"""Unit tests — conflict-detection routing logic."""

from __future__ import annotations

import pytest

from trip_planner.models.proposal import BudgetOutput, PlanOutput, ResearchOutput, TripProposal
from trip_planner.models.request import TripRequest
from trip_planner.models.validation import ROUTE_FINALIZE, ROUTE_OPTIMIZE
from trip_planner.workflow.router import validate_and_route
from trip_planner.workflow.state import WorkflowState


def _make_state(conflict_flags: list, budget_usd: float = 2600, total_estimate: float = 1800) -> WorkflowState:
    request = TripRequest(destination="Kyoto", month="October", budget_usd=budget_usd)
    proposal = TripProposal(
        request=request,
        research=ResearchOutput(),
        itinerary=PlanOutput(conflict_flags=conflict_flags),
        budget=BudgetOutput(total_estimate=total_estimate),
    )
    state = WorkflowState(request=request)
    state.proposal = proposal
    return state


@pytest.mark.asyncio
class TestConflictRouting:
    async def test_no_conflicts_routes_to_finalize(self):
        state = _make_state(conflict_flags=[])
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_FINALIZE
        assert not state.validation.has_schedule_conflicts

    async def test_single_conflict_routes_to_optimize(self):
        state = _make_state(conflict_flags=["Day 1: 09:00-11:00 overlaps with 10:00-12:00"])
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE
        assert state.validation.has_schedule_conflicts

    async def test_multiple_conflicts_captured_in_reasons(self):
        flags = ["Conflict A", "Conflict B"]
        state = _make_state(conflict_flags=flags)
        state = await validate_and_route(state)
        combined = " ".join(state.validation.reasons)
        assert "Conflict A" in combined
        assert "Conflict B" in combined

    async def test_conflict_AND_over_budget_both_captured(self):
        state = _make_state(
            conflict_flags=["Overlap on day 2"],
            budget_usd=600,
            total_estimate=1800,
        )
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE
        assert state.validation.has_schedule_conflicts
        assert state.validation.is_over_budget

    async def test_conflict_without_budget_overrun_still_routes_to_optimize(self):
        state = _make_state(conflict_flags=["Day 3 morning conflict"], budget_usd=2600, total_estimate=1800)
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE
        assert not state.validation.is_over_budget
