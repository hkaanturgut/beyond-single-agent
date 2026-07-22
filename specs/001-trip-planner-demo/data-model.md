# Data Model: Beyond a Single Agent — Trip Planner Demo

## Entities

## TripRequest

- **Description**: Parsed user intent for a 3-day trip.
- **Fields**:
  - `destination` (string, required)
  - `month` (string, required)
  - `budget_usd` (number, required, > 0)
  - `preferences` (list[string], optional)
  - `created_at` (datetime)
- **Validation**:
  - Destination cannot be empty.
  - Month must be recognized in a supported month format.
  - Budget must be positive.

## ResearchOutput

- **Description**: Destination intelligence gathered by the researcher.
- **Fields**:
  - `attractions` (list[string])
  - `weather_summary` (string)
  - `events` (list[string])
  - `cultural_tips` (list[string])
  - `sources` (list[string], optional)

## PlanOutput

- **Description**: Draft itinerary created by planning specialist.
- **Fields**:
  - `days` (list[DayPlan], exactly 3 entries)
  - `conflict_flags` (list[string])

### DayPlan

- `day_number` (int: 1..3)
- `slots` (list[TimeSlot])

### TimeSlot

- `start_time` (string)
- `end_time` (string)
- `activity` (string)
- `location_hint` (string, optional)

## BudgetOutput

- **Description**: Cost estimate from budget specialist.
- **Fields**:
  - `flight_estimate` (number)
  - `hotel_estimate` (number)
  - `food_estimate` (number)
  - `activity_estimate` (number)
  - `total_estimate` (number)
  - `confidence` (string: low|medium|high)

## TripProposal

- **Description**: Aggregated output from fan-in stage.
- **Fields**:
  - `request` (TripRequest)
  - `research` (ResearchOutput)
  - `itinerary` (PlanOutput)
  - `budget` (BudgetOutput)

## ValidationResult

- **Description**: Routing decision input.
- **Fields**:
  - `is_over_budget` (bool)
  - `has_schedule_conflicts` (bool)
  - `route` (string: optimize|finalize)
  - `reasons` (list[string])

## OptimizedProposal

- **Description**: Proposal adjusted to reduce cost/conflicts.
- **Fields**:
  - `proposal` (TripProposal)
  - `changes_applied` (list[string])
  - `remaining_tradeoffs` (list[string])

## FinalTripBrief

- **Description**: Final end-user artifact.
- **Fields**:
  - `markdown` (string)
  - `output_path` (string)
  - `generated_at` (datetime)

## Relationships

- `TripRequest` -> drives all specialist outputs.
- `ResearchOutput`, `PlanOutput`, `BudgetOutput` -> aggregate into `TripProposal`.
- `TripProposal` -> evaluated into `ValidationResult`.
- `ValidationResult.route == optimize` -> produces `OptimizedProposal` -> final brief.
- `ValidationResult.route == finalize` -> `TripProposal` directly becomes final brief.

