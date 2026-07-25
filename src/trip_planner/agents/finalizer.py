"""FinalizerAgent — renders the polished markdown trip brief."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from urllib.parse import quote_plus

from trip_planner.backends.base import BackendAdapter
from trip_planner.models import FinalTripBrief
from trip_planner.models.proposal import (
    BudgetOutput,
    DayPlan,
    OptimizedProposal,
    TripProposal,
)
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("agents.finalizer")

# Explicit hosted-agent name (matches scripts/deploy_agents.py registration).
AGENT_NAME = "finalizer-agent"

_SYSTEM = (
    "You are a travel writer. "
    "Given trip research, an itinerary, and a budget breakdown, "
    "write a packing/preparation section of 4-6 bullet points appropriate "
    "for the destination and month.  Return plain text bullets only."
)


def _maps_link(query: str) -> str:
    """Deterministic Google Maps search link for a place/query."""
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)


def _weather_link(destination: str, month: str) -> str:
    """Deterministic weather/forecast search link for the destination and month."""
    return "https://www.google.com/search?q=" + quote_plus(f"{destination} weather {month}")


def _linked(name: str, url: Optional[str]) -> str:
    """Render ``[name](url)`` when a URL is present, else the plain name."""
    return f"[{name}]({url})" if url else name


def _make_tips_prompt(proposal: TripProposal) -> str:
    return (
        f"Destination: {proposal.request.destination}\n"
        f"Month: {proposal.request.month}\n"
        f"Weather: {proposal.research.weather_summary}\n"
        "Give me 4-6 packing and preparation tips for this trip."
    )


def _render_markdown(
    proposal: TripProposal,
    packing_tips: str,
    optimized: Optional[OptimizedProposal],
) -> str:
    dest = proposal.request.destination
    month = proposal.request.month
    budget = proposal.budget

    lines: List[str] = [
        f"# Trip Brief: {dest} — {month}",
        "",
        "## Trip Overview",
        "",
        f"**Destination**: {dest}  ",
        f"**Month**: {month}  ",
        f"**Budget**: ${proposal.request.budget_usd:.0f} USD  ",
        f"**Duration**: 3 days  ",
        "",
    ]

    # --- Research highlights ---
    research = proposal.research
    if research.weather_summary:
        weather_url = research.weather_url or _weather_link(dest, month)
        lines += [
            f"**Weather**: {research.weather_summary} ([forecast]({weather_url}))",
            "",
        ]
    if research.attraction_links or research.attractions:
        if research.attraction_links:
            rendered = [
                _linked(i.name, i.url or _maps_link(f"{i.name} {dest}"))
                for i in research.attraction_links
            ]
        else:
            rendered = [
                _linked(name, _maps_link(f"{name} {dest}"))
                for name in research.attractions
            ]
        lines += ["**Top attractions**: " + ", ".join(rendered), ""]
    if research.event_links or research.events:
        if research.event_links:
            rendered = [_linked(i.name, i.url) for i in research.event_links]
        else:
            rendered = list(research.events)
        lines += ["**Events this month**: " + ", ".join(rendered), ""]

    # --- Itinerary ---
    lines += ["## Day-by-Day Itinerary", ""]
    for day in sorted(proposal.itinerary.days, key=lambda d: d.day_number):
        lines += [f"### Day {day.day_number}", ""]
        for slot in day.slots:
            hint = f" — *{slot.location_hint}*" if slot.location_hint else ""
            place = slot.location_hint or slot.activity
            map_url = _maps_link(f"{place} {dest}")
            lines.append(
                f"- **{slot.start_time}–{slot.end_time}**: {slot.activity}{hint} · [🗺️ map]({map_url})"
            )
        lines.append("")

    # --- Budget ---
    lines += [
        "## Budget Breakdown",
        "",
        "| Category | Estimate (USD) |",
        "|---|---|",
        f"| ✈️  Flights | ${budget.flight_estimate:.0f} |",
        f"| 🏨 Hotel (3 nights) | ${budget.hotel_estimate:.0f} |",
        f"| 🍽️  Food (3 days) | ${budget.food_estimate:.0f} |",
        f"| 🎭 Activities | ${budget.activity_estimate:.0f} |",
        f"| **Total** | **${budget.total_estimate:.0f}** |",
        "",
        f"*Cost estimate confidence: {budget.confidence}*",
        "",
    ]

    # --- Cultural tips ---
    if proposal.research.cultural_tips:
        lines += ["## Cultural Tips", ""]
        for tip in proposal.research.cultural_tips:
            lines.append(f"- {tip}")
        lines.append("")

    # --- Sources ---
    if proposal.research.sources:
        lines += ["## Sources", ""]
        for src in proposal.research.sources:
            src = src.strip()
            if not src:
                continue
            lines.append(f"- <{src}>" if src.startswith("http") else f"- {src}")
        lines.append("")

    # --- Packing / Prep ---
    lines += ["## Packing / Preparation Tips", ""]
    for tip_line in packing_tips.splitlines():
        cleaned = tip_line.strip()
        if cleaned:
            lines.append(cleaned if cleaned.startswith("-") else f"- {cleaned}")
    lines.append("")

    # --- Optimization notes (only when optimizer route was used) ---
    if optimized is not None:
        lines += ["## Optimization Notes", ""]
        if optimized.changes_applied:
            lines += ["**Adjustments applied:**", ""]
            for change in optimized.changes_applied:
                lines.append(f"- {change}")
            lines.append("")
        if optimized.remaining_tradeoffs:
            lines += ["**Remaining trade-offs:**", ""]
            for tradeoff in optimized.remaining_tradeoffs:
                lines.append(f"- {tradeoff}")
            lines.append("")

    lines += [
        "---",
        f"*Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*",
    ]
    return "\n".join(lines)


class FinalizerAgent:
    """Produces the polished markdown trip brief."""

    def __init__(self, backend: BackendAdapter) -> None:
        self._backend = backend

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Populate ``state.final_brief``."""
        with stage_span(_log, "FinalizerAgent"):
            proposal = state.proposal
            if proposal is None:
                _log.error("FinalizerAgent called without a proposal")
                return state

            # Determine whether we are on the optimized path
            optimized = state.optimized
            # If optimized, use its revised proposal as the source of truth
            effective_proposal = optimized.proposal if optimized else proposal

            # Ask the model for packing tips (non-blocking if it fails)
            try:
                packing_tips = await self._backend.generate(
                    system_prompt=_SYSTEM,
                    user_message=_make_tips_prompt(effective_proposal),
                    max_tokens=400,
                    agent_name=AGENT_NAME,
                )
            except Exception as exc:
                _log.warning("FinalizerAgent: packing tips call failed (%s); using defaults", exc)
                packing_tips = (
                    "- Pack light layers for variable weather.\n"
                    "- Carry copies of travel documents.\n"
                    "- Download offline maps.\n"
                    "- Bring a small first-aid kit."
                )

            markdown = _render_markdown(effective_proposal, packing_tips, optimized)
            # output_path is filled in by the runner after writing the file
            state.final_brief = FinalTripBrief(
                markdown=markdown,
                output_path="",  # placeholder; runner sets the real path
            )
        return state
