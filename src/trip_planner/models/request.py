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

_MONTH_ALT = "|".join(VALID_MONTHS)

# Destination + month: "trip to <destination> in <month>" — the month must be a
# real month name, so an optional trailing year (e.g. "October 2026") or extra
# words after it don't interfere.
_DEST_MONTH_PATTERN = re.compile(
    r"trip to\s+(.+?)\s+in\s+(" + _MONTH_ALT + r")\b",
    re.IGNORECASE,
)

# Fallbacks used when the combined pattern doesn't match.
_MONTH_PATTERN = re.compile(r"\b(" + _MONTH_ALT + r")\b", re.IGNORECASE)
_DEST_ONLY_PATTERN = re.compile(r"trip to\s+(.+?)\s+in\b", re.IGNORECASE)

# Budget: first number following the word "budget" (allowing a currency symbol
# or code in between, e.g. "budget $2500", "budget of USD 2,500.50"). Falls back
# to any "$<amount>" anywhere in the prompt.
_BUDGET_PATTERN = re.compile(
    r"budget\b[^\d]*?([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
_DOLLAR_AMOUNT_PATTERN = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")


def parse_trip_request(prompt: str) -> TripRequest:
    """Parse a natural-language trip prompt into a :class:`TripRequest`.

    The parser is intentionally lenient. It extracts three fields independently
    so that extra words, a trailing year, or a currency code don't break it. All
    of the following work::

        Plan my 3-day trip to Valletta in April with budget $2200
        Plan my trip to Japan in October 2026 with budget $2500 CAD per person
        I'd love a trip to Lisbon in May, budget of USD 1,800

    The day count and currency are informational only — this demo always plans a
    3-day trip and treats the numeric budget as USD.

    Raises:
        ValueError: if a destination, month, and budget cannot all be found.
    """
    text = prompt.strip()

    # 1. Destination + month (preferred single match keeps them aligned).
    destination: Optional[str] = None
    month: Optional[str] = None
    dm = _DEST_MONTH_PATTERN.search(text)
    if dm:
        destination = dm.group(1).strip()
        month = dm.group(2).strip()
    else:
        dest_only = _DEST_ONLY_PATTERN.search(text)
        if dest_only:
            destination = dest_only.group(1).strip()
        month_match = _MONTH_PATTERN.search(text)
        if month_match:
            month = month_match.group(1).strip()

    # 2. Budget.
    budget_match = _BUDGET_PATTERN.search(text) or _DOLLAR_AMOUNT_PATTERN.search(text)
    budget_value = budget_match.group(1).replace(",", "") if budget_match else None

    missing = [
        name
        for name, value in (
            ("destination", destination),
            ("month", month),
            ("budget", budget_value),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            "Could not parse "
            + ", ".join(missing)
            + " from the request. Include a destination, a month, and a budget, "
            "e.g. 'Plan my 3-day trip to <destination> in <month> "
            "with budget $<amount>'."
        )

    return TripRequest(
        destination=destination.title(),  # type: ignore[union-attr]
        month=month.capitalize(),  # type: ignore[union-attr]
        budget_usd=float(budget_value),  # type: ignore[arg-type]
    )
