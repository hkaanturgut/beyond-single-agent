"""FinalizerAgent — renders the polished markdown trip brief."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

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

_SYSTEM = (
    "You are a travel writer. "
    "Given trip research, an itinerary, and a budget breakdown, "
    "write a packing/preparation section of 4-6 bullet points appropriate "
    "for the destination and month.  Return plain text bullets only."
)


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
    if proposal.research.weather_summary:
        lines += ["**Weather**: " + proposal.research.weather_summary, ""]
    if proposal.research.attractions:
        lines += ["**Top attractions**: " + ", ".join(proposal.research.attractions), ""]
    if proposal.research.events:
        lines += ["**Events this month**: " + ", ".join(proposal.research.events), ""]

    # --- Itinerary ---
    lines += ["## Day-by-Day Itinerary", ""]
    for day in sorted(proposal.itinerary.days, key=lambda d: d.day_number):
        lines += [f"### Day {day.day_number}", ""]
        for slot in day.slots:
            hint = f" — *{slot.location_hint}*" if slot.location_hint else ""
            lines.append(
                f"- **{slot.start_time}–{slot.end_time}**: {slot.activity}{hint}"
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
