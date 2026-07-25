"""ResearcherAgent — gathers destination intelligence concurrently."""

from __future__ import annotations

import json
import re
from typing import List

from trip_planner.backends.base import BackendAdapter
from trip_planner.models.proposal import ResearchOutput
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("agents.researcher")

# Explicit hosted-agent name (matches scripts/deploy_agents.py registration).
AGENT_NAME = "researcher-agent"

_SYSTEM = (
    "You are a travel research specialist. "
    "Given a destination and travel month, provide a concise JSON object with keys: "
    "attractions (list of 4-6 top sights), weather_summary (1-2 sentences), "
    "events (list of notable events that month), cultural_tips (list of 3-4 tips). "
    "Return ONLY valid JSON, no markdown fences."
)


def _make_prompt(destination: str, month: str) -> str:
    return (
        f"Research destination: {destination}\n"
        f"Travel month: {month}\n"
        "Return a JSON object with keys: attractions, weather_summary, events, cultural_tips."
    )


def _parse_response(raw: str) -> ResearchOutput:
    """Extract JSON from the model response, falling back to an empty output."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Find the outermost JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        _log.warning("ResearcherAgent: no JSON found in response; using defaults")
        return ResearchOutput(
            weather_summary=raw[:200] if raw else "Weather information unavailable.",
        )
    try:
        data = json.loads(cleaned[start:end])
        return ResearchOutput(
            attractions=_to_list(data.get("attractions")),
            weather_summary=str(data.get("weather_summary", "")),
            events=_to_list(data.get("events")),
            cultural_tips=_to_list(data.get("cultural_tips")),
        )
    except (json.JSONDecodeError, TypeError) as exc:
        _log.warning("ResearcherAgent: JSON parse error (%s); using partial data", exc)
        return ResearchOutput(weather_summary=raw[:200])


def _to_list(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value]
    return []


class ResearcherAgent:
    """Queries the backend for destination intelligence."""

    def __init__(self, backend: BackendAdapter) -> None:
        self._backend = backend

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Populate ``state.research_output``."""
        with stage_span(_log, "ResearcherAgent"):
            try:
                raw = await self._backend.generate(
                    system_prompt=_SYSTEM,
                    user_message=_make_prompt(
                        state.request.destination, state.request.month
                    ),
                    max_tokens=800,
                    agent_name=AGENT_NAME,
                )
                state.research_output = _parse_response(raw)
            except Exception as exc:
                _log.error("ResearcherAgent failed: %s", exc)
                state.record_error("researcher", exc)
                state.research_output = ResearchOutput(
                    weather_summary="Research unavailable — backend error."
                )
        return state
