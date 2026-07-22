"""PlannerAgent — drafts the day-by-day itinerary."""

from __future__ import annotations

import json
import re
from typing import Dict, List

from trip_planner.backends.base import BackendAdapter
from trip_planner.models.proposal import DayPlan, PlanOutput, TimeSlot
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("agents.planner")

_SYSTEM = (
    "You are a trip-planning specialist. "
    "Given a destination, travel month, budget, and research notes, "
    "draft a 3-day itinerary as a JSON object with keys: "
    "days (array of 3 day objects, each with day_number (1-3) and slots "
    "(array of {start_time, end_time, activity, location_hint})), "
    "conflict_flags (array of strings describing any scheduling conflicts). "
    "Keep time slots realistic (no overlaps within a day). "
    "Return ONLY valid JSON, no markdown fences."
)


def _make_prompt(state: WorkflowState) -> str:
    research = state.research_output
    attractions = ", ".join(research.attractions[:4]) if research else "N/A"
    return (
        f"Destination: {state.request.destination}\n"
        f"Month: {state.request.month}\n"
        f"Budget: ${state.request.budget_usd:.0f}\n"
        f"Key attractions: {attractions}\n"
        "Draft a 3-day itinerary JSON."
    )


def _safe_slot(raw: Dict) -> TimeSlot:
    return TimeSlot(
        start_time=str(raw.get("start_time", "09:00")),
        end_time=str(raw.get("end_time", "10:00")),
        activity=str(raw.get("activity", "Explore the area")),
        location_hint=raw.get("location_hint"),
    )


def _parse_response(raw: str) -> PlanOutput:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        _log.warning("PlannerAgent: no JSON found; returning default 3-day plan")
        return _default_plan()
    try:
        data = json.loads(cleaned[start:end])
        days = []
        for d in data.get("days", []):
            slots = [_safe_slot(s) for s in d.get("slots", [])]
            days.append(DayPlan(day_number=int(d.get("day_number", 1)), slots=slots))
        if not days:
            days = _default_days()
        return PlanOutput(
            days=days,
            conflict_flags=[str(f) for f in data.get("conflict_flags", [])],
        )
    except (json.JSONDecodeError, TypeError, KeyError) as exc:
        _log.warning("PlannerAgent: parse error (%s); returning default plan", exc)
        return _default_plan()


def _default_days() -> List[DayPlan]:
    return [
        DayPlan(day_number=i, slots=[
            TimeSlot(start_time="09:00", end_time="12:00", activity="Morning sightseeing"),
            TimeSlot(start_time="13:00", end_time="17:00", activity="Afternoon exploration"),
        ])
        for i in range(1, 4)
    ]


def _default_plan() -> PlanOutput:
    return PlanOutput(days=_default_days(), conflict_flags=[])


class PlannerAgent:
    """Drafts the 3-day itinerary."""

    def __init__(self, backend: BackendAdapter) -> None:
        self._backend = backend

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Populate ``state.plan_output``."""
        with stage_span(_log, "PlannerAgent"):
            try:
                raw = await self._backend.generate(
                    system_prompt=_SYSTEM,
                    user_message=_make_prompt(state),
                    max_tokens=1200,
                )
                state.plan_output = _parse_response(raw)
            except Exception as exc:
                _log.error("PlannerAgent failed: %s", exc)
                state.record_error("planner", exc)
                state.plan_output = _default_plan()
        return state
