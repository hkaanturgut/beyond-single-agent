"""Typed proposal models produced by each specialist agent and the fan-in aggregator."""

from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from trip_planner.models.request import TripRequest


# ---------------------------------------------------------------------------
# Specialist outputs
# ---------------------------------------------------------------------------


class LinkedItem(BaseModel):
    """A named item with an optional source/reference URL."""

    name: str
    url: Optional[str] = None


class ResearchOutput(BaseModel):
    """Destination intelligence gathered by ResearcherAgent."""

    attractions: List[str] = []
    weather_summary: str = ""
    weather_url: Optional[str] = None
    events: List[str] = []
    cultural_tips: List[str] = []
    sources: List[str] = []
    # Rich, link-carrying variants (preferred by the renderer when present).
    attraction_links: List[LinkedItem] = []
    event_links: List[LinkedItem] = []


class TimeSlot(BaseModel):
    """A single activity slot within a day plan."""

    start_time: str
    end_time: str
    activity: str
    location_hint: Optional[str] = None


class DayPlan(BaseModel):
    """Schedule for one day of the trip (day_number: 1..3)."""

    day_number: int
    slots: List[TimeSlot] = []


class PlanOutput(BaseModel):
    """Draft itinerary created by PlannerAgent."""

    days: List[DayPlan] = Field(default_factory=list)
    conflict_flags: List[str] = []


class BudgetOutput(BaseModel):
    """Cost estimate from BudgetAgent."""

    flight_estimate: float = 0.0
    hotel_estimate: float = 0.0
    food_estimate: float = 0.0
    activity_estimate: float = 0.0
    total_estimate: float = 0.0
    confidence: str = "low"  # low | medium | high


# ---------------------------------------------------------------------------
# Aggregated proposal
# ---------------------------------------------------------------------------


class TripProposal(BaseModel):
    """Fan-in aggregate that combines all specialist outputs."""

    proposal_id: str = Field(default_factory=lambda: f"trip-{uuid4().hex[:8]}")
    request: TripRequest
    research: ResearchOutput = Field(default_factory=ResearchOutput)
    itinerary: PlanOutput = Field(default_factory=PlanOutput)
    budget: BudgetOutput = Field(default_factory=BudgetOutput)


# ---------------------------------------------------------------------------
# Optional optimised variant
# ---------------------------------------------------------------------------


class OptimizedProposal(BaseModel):
    """Revised proposal with documented adjustments and remaining trade-offs."""

    proposal: TripProposal
    changes_applied: List[str] = []
    remaining_tradeoffs: List[str] = []
