"""Routing decision logic — evaluates a TripProposal and chooses a branch.

This module produces the ``ValidationResult`` that drives the
``add_multi_selection_edge_group`` selector in the workflow builder.
"""

from __future__ import annotations

from trip_planner.models.validation import ROUTE_FINALIZE, ROUTE_OPTIMIZE, ValidationResult
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("workflow.router")


async def validate_and_route(state: WorkflowState) -> WorkflowState:
    """Populate ``state.validation`` with routing decision and reasons."""
    with stage_span(_log, "validate_and_route"):
        proposal = state.proposal
        if proposal is None:
            _log.warning("validate_and_route called before aggregation; defaulting to finalize")
            state.validation = ValidationResult(route=ROUTE_FINALIZE)
            return state

        reasons: list = []
        is_over_budget = False
        has_conflicts = False

        # --- Budget check ---
        budget_limit = proposal.request.budget_usd
        estimated = proposal.budget.total_estimate
        if estimated > budget_limit:
            is_over_budget = True
            reasons.append(
                f"Estimated cost ${estimated:.0f} exceeds budget ${budget_limit:.0f} "
                f"by ${estimated - budget_limit:.0f}."
            )

        # --- Conflict check ---
        if proposal.itinerary.conflict_flags:
            has_conflicts = True
            for flag in proposal.itinerary.conflict_flags:
                reasons.append(f"Schedule conflict: {flag}")

        route = ROUTE_OPTIMIZE if (is_over_budget or has_conflicts) else ROUTE_FINALIZE
        state.validation = ValidationResult(
            is_over_budget=is_over_budget,
            has_schedule_conflicts=has_conflicts,
            route=route,
            reasons=reasons,
        )
        _log.info("route decision: %s (over_budget=%s, conflicts=%s)", route, is_over_budget, has_conflicts)
    return state


def route_selector(state: WorkflowState) -> str:
    """Return the branch key from the current validation result.

    Used as the ``selector`` argument to ``add_multi_selection_edge_group``.
    """
    if state.validation is None:
        return ROUTE_FINALIZE
    return state.validation.route
