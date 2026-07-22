"""Unit tests — budget-threshold routing logic."""

from __future__ import annotations

import pytest

from trip_planner.models.proposal import BudgetOutput, PlanOutput, ResearchOutput, TripProposal
from trip_planner.models.request import TripRequest
from trip_planner.models.validation import ROUTE_FINALIZE, ROUTE_OPTIMIZE
from trip_planner.workflow.router import route_selector, validate_and_route
from trip_planner.workflow.state import WorkflowState


def _make_state(budget_usd: float, total_estimate: float, conflict_flags=None) -> WorkflowState:
    request = TripRequest(destination="Lisbon", month="May", budget_usd=budget_usd)
    proposal = TripProposal(
        request=request,
        research=ResearchOutput(),
        itinerary=PlanOutput(conflict_flags=conflict_flags or []),
        budget=BudgetOutput(total_estimate=total_estimate),
    )
    state = WorkflowState(request=request)
    state.proposal = proposal
    return state


@pytest.mark.asyncio
class TestBudgetRouting:
    async def test_within_budget_routes_to_finalize(self):
        state = _make_state(budget_usd=2600, total_estimate=1800)
        state = await validate_and_route(state)
        assert state.validation is not None
        assert state.validation.route == ROUTE_FINALIZE
        assert not state.validation.is_over_budget

    async def test_over_budget_routes_to_optimize(self):
        state = _make_state(budget_usd=600, total_estimate=1800)
        state = await validate_and_route(state)
        assert state.validation is not None
        assert state.validation.route == ROUTE_OPTIMIZE
        assert state.validation.is_over_budget

    async def test_exactly_at_budget_routes_to_finalize(self):
        state = _make_state(budget_usd=1800, total_estimate=1800)
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_FINALIZE

    async def test_one_cent_over_budget_routes_to_optimize(self):
        state = _make_state(budget_usd=1800, total_estimate=1800.01)
        state = await validate_and_route(state)
        assert state.validation.route == ROUTE_OPTIMIZE

    async def test_validation_includes_reason_for_overrun(self):
        state = _make_state(budget_usd=600, total_estimate=1800)
        state = await validate_and_route(state)
        reasons_text = " ".join(state.validation.reasons)
        assert "1800" in reasons_text or "over" in reasons_text.lower()

    async def test_route_selector_returns_correct_key(self):
        state = _make_state(budget_usd=600, total_estimate=1800)
        state = await validate_and_route(state)
        assert route_selector(state) == ROUTE_OPTIMIZE

    async def test_route_selector_on_state_without_validation(self):
        state = WorkflowState(request=TripRequest(
            destination="Lisbon", month="May", budget_usd=2600
        ))
        assert route_selector(state) == ROUTE_FINALIZE
