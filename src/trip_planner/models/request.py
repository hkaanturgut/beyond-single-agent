"""Typed request model and natural-language parser for trip planning prompts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

VALID_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Canonical month capitalisation (index 0 = January)
_MONTH_CAPS = [m.capitalize() for m in VALID_MONTHS]


class TripRequest(BaseModel):
    """Parsed user intent for a 3-day trip."""

    destination: str
    month: str
    budget_usd: float
    preferences: List[str] = []
    created_at: datetime = datetime.utcnow()

    @field_validator("destination")
    @classmethod
    def destination_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("destination cannot be empty")
        return stripped

    @field_validator("month")
    @classmethod
    def month_must_be_valid(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in VALID_MONTHS:
            raise ValueError(
                f"month must be one of: {', '.join(_MONTH_CAPS)}"
            )
        return normalised.capitalize()

    @field_validator("budget_usd")
    @classmethod
    def budget_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("budget_usd must be a positive number")
        return v

    @property
    def safe_destination(self) -> str:
        """Filesystem-safe version of the destination string."""
        return re.sub(r"[^\w\-]", "-", self.destination.lower()).strip("-")


# ---------------------------------------------------------------------------
# Natural-language parser
# ---------------------------------------------------------------------------

_PROMPT_PATTERN = re.compile(
    r"plan my (?:\d+-day )?trip to (.+?) in (\w+) with budget \$?([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)


def parse_trip_request(prompt: str) -> TripRequest:
    """Parse a natural-language trip prompt into a :class:`TripRequest`.

    Expected format (case-insensitive)::

        Plan my 3-day trip to <destination> in <month> with budget $<amount>

    Raises:
        ValueError: if the prompt does not match the expected pattern or if
            any extracted field fails validation.
    """
    match = _PROMPT_PATTERN.search(prompt.strip())
    if not match:
        raise ValueError(
            "Could not parse request. "
            "Use format: 'Plan my 3-day trip to <destination> in <month> "
            "with budget $<amount>'"
        )

    destination = match.group(1).strip().title()
    month = match.group(2).strip().capitalize()
    budget_str = match.group(3).replace(",", "")

    return TripRequest(
        destination=destination,
        month=month,
        budget_usd=float(budget_str),
    )
