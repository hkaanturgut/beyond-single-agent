"""Shared workflow state object that is threaded through all stages.

The state is a plain dataclass (not a Pydantic model) because it is mutated
in-place by each stage function and never serialised directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from trip_planner.models.proposal import (
    BudgetOutput,
    OptimizedProposal,
    PlanOutput,
    ResearchOutput,
    TripProposal,
)
from trip_planner.models.request import TripRequest
from trip_planner.models.validation import ValidationResult
from trip_planner.models import FinalTripBrief


@dataclass
class WorkflowState:
    """Carries all intermediate and final results through the pipeline."""

    request: TripRequest

    # --- Fan-out outputs (populated concurrently) ---
    research_output: Optional[ResearchOutput] = None
    plan_output: Optional[PlanOutput] = None
    budget_output: Optional[BudgetOutput] = None

    # --- Aggregation ---
    proposal: Optional[TripProposal] = None

    # --- Routing ---
    validation: Optional[ValidationResult] = None

    # --- Optimisation (only when routed that way) ---
    optimized: Optional[OptimizedProposal] = None

    # --- Final output ---
    final_brief: Optional[FinalTripBrief] = None

    # --- Metadata ---
    backend_name: str = "unknown"
    errors: list = field(default_factory=list)

    def record_error(self, stage: str, exc: Exception) -> None:
        """Append a non-fatal error to the error log."""
        self.errors.append({"stage": stage, "error": str(exc)})
