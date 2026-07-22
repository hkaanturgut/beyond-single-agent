"""Validation model and routing decision logic."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

ROUTE_OPTIMIZE = "optimize"
ROUTE_FINALIZE = "finalize"


class ValidationResult(BaseModel):
    """Constraint evaluation used to decide the workflow route.

    ``route`` is always one of ``"optimize"`` or ``"finalize"``.
    """

    is_over_budget: bool = False
    has_schedule_conflicts: bool = False
    route: str = ROUTE_FINALIZE
    reasons: List[str] = []
