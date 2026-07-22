"""BudgetAgent — produces cost estimates for the trip."""

from __future__ import annotations

import json
import re

from trip_planner.backends.base import BackendAdapter
from trip_planner.models.proposal import BudgetOutput
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("agents.budget")

_SYSTEM = (
    "You are a travel budget specialist. "
    "Given a destination, travel month, and budget limit, "
    "estimate costs as a JSON object with keys: "
    "flight_estimate (number), hotel_estimate (number, 3 nights), "
    "food_estimate (number, 3 days), activity_estimate (number), "
    "total_estimate (sum of the above), "
    "confidence (low|medium|high based on data availability). "
    "All values are in USD. Return ONLY valid JSON, no markdown fences."
)


def _make_prompt(state: WorkflowState) -> str:
    return (
        f"Destination: {state.request.destination}\n"
        f"Month: {state.request.month}\n"
        f"Budget limit: ${state.request.budget_usd:.0f} USD\n"
        "Estimate flight, hotel (3 nights), food (3 days), and activities costs."
    )


def _parse_response(raw: str, budget_limit: float) -> BudgetOutput:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        _log.warning("BudgetAgent: no JSON found; using proportional defaults")
        return _proportional_defaults(budget_limit)
    try:
        data = json.loads(cleaned[start:end])
        flight = float(data.get("flight_estimate", 0))
        hotel = float(data.get("hotel_estimate", 0))
        food = float(data.get("food_estimate", 0))
        activities = float(data.get("activity_estimate", 0))
        # Honour total if provided; otherwise sum the parts
        total = float(data.get("total_estimate", flight + hotel + food + activities))
        confidence = str(data.get("confidence", "low")).lower()
        if confidence not in ("low", "medium", "high"):
            confidence = "low"
        return BudgetOutput(
            flight_estimate=flight,
            hotel_estimate=hotel,
            food_estimate=food,
            activity_estimate=activities,
            total_estimate=total,
            confidence=confidence,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        _log.warning("BudgetAgent: parse error (%s); using proportional defaults", exc)
        return _proportional_defaults(budget_limit)


def _proportional_defaults(budget: float) -> BudgetOutput:
    """Return a rough proportional split as a fallback."""
    flight = round(budget * 0.30, 2)
    hotel = round(budget * 0.30, 2)
    food = round(budget * 0.20, 2)
    activity = round(budget * 0.15, 2)
    return BudgetOutput(
        flight_estimate=flight,
        hotel_estimate=hotel,
        food_estimate=food,
        activity_estimate=activity,
        total_estimate=round(flight + hotel + food + activity, 2),
        confidence="low",
    )


class BudgetAgent:
    """Estimates trip costs."""

    def __init__(self, backend: BackendAdapter) -> None:
        self._backend = backend

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Populate ``state.budget_output``."""
        with stage_span(_log, "BudgetAgent"):
            try:
                raw = await self._backend.generate(
                    system_prompt=_SYSTEM,
                    user_message=_make_prompt(state),
                    max_tokens=600,
                )
                state.budget_output = _parse_response(raw, state.request.budget_usd)
            except Exception as exc:
                _log.error("BudgetAgent failed: %s", exc)
                state.record_error("budget", exc)
                state.budget_output = _proportional_defaults(state.request.budget_usd)
        return state
