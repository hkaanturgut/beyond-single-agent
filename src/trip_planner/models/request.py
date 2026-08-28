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

# Month anywhere in the prompt (optional). A trailing year or extra words after
# it (e.g. "October 2026") don't interfere.
_MONTH_PATTERN = re.compile(r"\b(" + _MONTH_ALT + r")\b", re.IGNORECASE)

# Destination: the words after "trip/travel/vacation/... to", stopping at the
# first structural keyword (from/in/on/for/with/,/budget) or the end of the
# string. This tolerates a missing month, an origin ("from Toronto"), a duration
# ("2 weeks"), and "per person" phrasing.
_DEST_PATTERN = re.compile(
    r"(?:trip|travel|traveling|travelling|vacation|holiday|getaway|visit|go(?:ing)?)"
    r"\s+to\s+(?P<dest>.+?)"
    r"(?=\s+(?:from|in|on|for|with|,|budget)\b|$)",
    re.IGNORECASE,
)

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

    The parser is intentionally lenient. It extracts each field independently so
    that extra words, an origin, a duration, a trailing year, or a currency code
    don't break it. Only a destination and a budget are required; the month is
    optional and defaults to the current month when omitted. All of the
    following work::

        Plan my 3-day trip to Valletta in April with budget $2200
        Plan my trip to Japan in October 2026 with budget $2500 CAD per person
        I'd love a trip to Lisbon in May, budget of USD 1,800
        Plan my 2 weeks trip to Japan from Toronto with $3500 per person

    The day count, origin, and currency are informational only — this demo always
    plans a 3-day trip and treats the numeric budget as USD.

    Raises:
        ValueError: if a destination or budget cannot be found.
    """
    text = prompt.strip()

    # 1. Destination.
    destination: Optional[str] = None
    dest_match = _DEST_PATTERN.search(text)
    if dest_match:
        destination = dest_match.group("dest").strip(" ,.")

    # 2. Month (optional — defaults to the current month when unspecified).
    month_match = _MONTH_PATTERN.search(text)
    if month_match:
        month = month_match.group(1).strip()
    else:
        month = _MONTH_CAPS[datetime.utcnow().month - 1]

    # 3. Budget.
    budget_match = _BUDGET_PATTERN.search(text) or _DOLLAR_AMOUNT_PATTERN.search(text)
    budget_value = budget_match.group(1).replace(",", "") if budget_match else None

    missing = [
        name
        for name, value in (
            ("destination", destination),
            ("budget", budget_value),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            "Could not parse "
            + ", ".join(missing)
            + " from the request. Include a destination and a budget (a month is "
            "optional), e.g. 'Plan my trip to <destination> with budget $<amount>'."
        )

    return TripRequest(
        destination=destination.title(),  # type: ignore[union-attr]
        month=month.capitalize(),
        budget_usd=float(budget_value),  # type: ignore[arg-type]
    )
