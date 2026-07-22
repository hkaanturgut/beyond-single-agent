# Quickstart Validation: Beyond a Single Agent — Trip Planner Demo

This guide validates the spec-defined behavior without implementing production logic yet.

## Prerequisites

- Python 3.11+
- Project dependencies installed
- Environment variables configured (`.env` based on `.env.example`)

## Validation Scenarios

## Scenario 1: Happy path (finalizer route)

1. Set backend mode to local-friendly.
2. Submit:
   - `Plan my 3-day trip to Lisbon in May with budget $2600`
3. Expected:
   - Workflow fan-out and fan-in complete.
   - Route decision is `finalize`.
   - Output file created in `output/` with required markdown sections.

## Scenario 2: Over-budget path (optimizer route)

1. Keep same destination/month but lower budget:
   - `Plan my 3-day trip to Lisbon in May with budget $600`
2. Expected:
   - Route decision is `optimize`.
   - Revised proposal produced before final output.
   - Output includes optimization notes/trade-offs.

## Scenario 3: Conflict-triggered optimization

1. Use test fixtures that intentionally create overlapping itinerary slots.
2. Expected:
   - `has_schedule_conflicts = true`
   - Route decision is `optimize`
   - Final output includes conflict-resolution notes.

## Scenario 4: Invalid input handling

1. Submit malformed request (missing budget).
2. Expected:
   - Validation error message with actionable correction guidance.
   - No output markdown file created.

## Scenario 5: Backend parity check

1. Run the same valid request in backend mode A and backend mode B.
2. Expected:
   - Both runs complete.
   - Both produce markdown briefs with the same required sections.

