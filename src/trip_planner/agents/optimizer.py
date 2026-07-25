"""OptimizerAgent — revises a TripProposal to reduce cost or resolve conflicts."""

from __future__ import annotations

from trip_planner.backends.base import BackendAdapter
from trip_planner.models.proposal import BudgetOutput, OptimizedProposal, TripProposal
from trip_planner.workflow.state import WorkflowState
from trip_planner.workflow.telemetry import get_logger, stage_span

_log = get_logger("agents.optimizer")

# Explicit hosted-agent name (matches scripts/deploy_agents.py registration).
AGENT_NAME = "optimizer-agent"

_SYSTEM = (
    "You are a trip optimisation specialist. "
    "Given an over-budget or conflict-containing trip proposal, suggest concrete "
    "adjustments.  Respond in plain text (not JSON) using this exact format:\n\n"
    "CHANGES_APPLIED:\n- <change 1>\n- <change 2>\n\n"
    "REMAINING_TRADEOFFS:\n- <tradeoff 1>\n- <tradeoff 2>\n\n"
    "REVISED_BUDGET:\n"
    "Flight: $<number>\n"
    "Hotel: $<number>\n"
    "Food: $<number>\n"
    "Activities: $<number>\n"
    "Total: $<number>\n"
    "Confidence: <low|medium|high>"
)


def _make_prompt(state: WorkflowState) -> str:
    proposal = state.proposal
    validation = state.validation
    if proposal is None or validation is None:
        return "No proposal available to optimise."

    budget = proposal.request.budget_usd
    total = proposal.budget.total_estimate
    reasons = "\n".join(f"- {r}" for r in validation.reasons) or "- (none specified)"
    return (
        f"Destination: {proposal.request.destination}\n"
        f"Month: {proposal.request.month}\n"
        f"Budget limit: ${budget:.0f}\n"
        f"Current estimated total: ${total:.0f}\n"
        f"Issues to resolve:\n{reasons}\n\n"
        "Please suggest optimisations."
    )


def _parse_optimizer_response(
    raw: str, original_proposal: TripProposal
) -> OptimizedProposal:
    """Extract structured changes from the optimizer's free-text response."""
    changes: list = []
    tradeoffs: list = []
    revised_budget = original_proposal.budget.model_copy()

    section = None
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("CHANGES_APPLIED:"):
            section = "changes"
        elif stripped.startswith("REMAINING_TRADEOFFS:"):
            section = "tradeoffs"
        elif stripped.startswith("REVISED_BUDGET:"):
            section = "budget"
        elif stripped.startswith("- ") and section == "changes":
            changes.append(stripped[2:])
        elif stripped.startswith("- ") and section == "tradeoffs":
            tradeoffs.append(stripped[2:])
        elif section == "budget" and ":" in stripped:
            key, _, val = stripped.partition(":")
            val = val.strip().lstrip("$").replace(",", "")
            try:
                amount = float(val)
                k = key.lower().strip()
                if "flight" in k:
                    revised_budget.flight_estimate = amount
                elif "hotel" in k:
                    revised_budget.hotel_estimate = amount
                elif "food" in k or "meal" in k:
                    revised_budget.food_estimate = amount
                elif "activ" in k:
                    revised_budget.activity_estimate = amount
                elif "total" in k:
                    revised_budget.total_estimate = amount
                elif "confidence" in k:
                    conf = val.strip().lower()
                    if conf in ("low", "medium", "high"):
                        revised_budget.confidence = conf
            except (ValueError, AttributeError):
                pass

    if not changes:
        changes = ["Adjustments applied — see revised budget above."]

    # Build a revised proposal with updated budget
    revised_proposal = original_proposal.model_copy(
        update={"budget": revised_budget}
    )
    return OptimizedProposal(
        proposal=revised_proposal,
        changes_applied=changes,
        remaining_tradeoffs=tradeoffs,
    )


class OptimizerAgent:
    """Revises a proposal to meet budget/conflict constraints."""

    def __init__(self, backend: BackendAdapter) -> None:
        self._backend = backend

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Populate ``state.optimized``."""
        with stage_span(_log, "OptimizerAgent"):
            proposal = state.proposal
            if proposal is None:
                _log.warning("OptimizerAgent: no proposal to optimise")
                return state
            try:
                raw = await self._backend.generate(
                    system_prompt=_SYSTEM,
                    user_message=_make_prompt(state),
                    max_tokens=4000,
                    agent_name=AGENT_NAME,
                )
                state.optimized = _parse_optimizer_response(raw, proposal)
            except Exception as exc:
                _log.error("OptimizerAgent failed: %s", exc)
                state.record_error("optimizer", exc)
                state.optimized = OptimizedProposal(
                    proposal=proposal,
                    changes_applied=["Optimisation unavailable — backend error."],
                    remaining_tradeoffs=["Manual review recommended."],
                )
        return state
