# Feature Specification: Beyond a Single Agent — Trip Planner Demo

**Feature Branch**: `001-trip-planner-demo`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "Plan my 3-day trip to <destination> in <month> with budget $<amount>; use concurrent specialist agents, fan-in aggregation, and conditional optimization before final markdown output."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate an initial 3-day trip proposal (Priority: P1)

As a traveler, I can request a destination/month/budget trip plan and receive a complete 3-day proposal with itinerary, cost estimate, and practical tips.

**Why this priority**: This is the core demo value and minimum end-to-end journey for both talks.

**Independent Test**: Submit one valid prompt and verify a complete markdown brief is generated and saved, including itinerary, budget breakdown, and prep tips.

**Acceptance Scenarios**:

1. **Given** a valid request with destination, month, and budget, **When** the workflow runs, **Then** the system produces a unified trip proposal combining research, schedule, and cost inputs.
2. **Given** a valid request, **When** the workflow finishes, **Then** a markdown file is saved to `output/` using the naming pattern `trip-<destination>-<timestamp>.md`.

---

### User Story 2 - Auto-adjust plans that violate constraints (Priority: P2)

As a traveler, when the initial proposal exceeds my budget or contains schedule conflicts, I receive a revised version that attempts to resolve those issues before final delivery.

**Why this priority**: The conditional branch is the key reason to use a multi-agent workflow instead of a single-response system.

**Independent Test**: Submit a deliberately low-budget request and confirm the workflow routes through an optimization step and returns a revised plan with documented adjustments.

**Acceptance Scenarios**:

1. **Given** an initial plan with total estimated cost above budget, **When** validation runs, **Then** the workflow routes to optimization before final output.
2. **Given** an initial plan with overlapping time slots, **When** validation runs, **Then** the workflow routes to optimization before final output.
3. **Given** a plan that cannot fully meet budget or conflict constraints, **When** optimization completes, **Then** the output clearly lists unresolved trade-offs.

---

### User Story 3 - Reuse the same workflow for two talk contexts (Priority: P3)

As a presenter, I can run the same trip-planner scenario in both a local-friendly mode and a production-oriented mode to support two different conference audiences.

**Why this priority**: Reusability across talks is a project goal, but secondary to the traveler outcome.

**Independent Test**: Run the workflow in both backend modes and confirm both produce comparable markdown outputs from the same user request.

**Acceptance Scenarios**:

1. **Given** backend mode A is selected, **When** a trip request is run, **Then** a full markdown brief is generated.
2. **Given** backend mode B is selected, **When** the same request is run, **Then** a full markdown brief is generated with the same required sections.

---

### Edge Cases

- User request is missing one or more required fields (destination, month, budget).
- Budget is non-numeric, zero, or negative.
- Destination string contains characters unsafe for file naming.
- Estimated costs are unavailable for one cost category.
- Initial itinerary contains conflicting or impossible time slots.
- Optimization cannot bring cost under budget while preserving a viable trip.
- No meaningful events or weather guidance is available for the requested month.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a natural-language request in the form "Plan my 3-day trip to `<destination>` in `<month>` with budget `$<amount>`" and extract the three required trip parameters.
- **FR-002**: System MUST run three specialist workstreams in parallel for research insights, itinerary drafting, and cost estimation.
- **FR-003**: System MUST aggregate specialist outputs into one unified proposal object before routing decisions.
- **FR-004**: System MUST evaluate aggregated output for budget overrun and itinerary conflicts.
- **FR-005**: System MUST route to an optimization step when budget overrun or schedule conflicts are detected.
- **FR-006**: System MUST route to a finalization step when no budget overrun and no schedule conflicts are detected.
- **FR-007**: System MUST produce a polished markdown trip brief containing (at minimum) itinerary, budget breakdown, and packing/prep tips.
- **FR-008**: System MUST save final output to `output/trip-<destination>-<timestamp>.md`.
- **FR-009**: System MUST support selecting one of two runtime backends via configuration so the same workflow can run in local-friendly and production-oriented contexts.
- **FR-010**: System MUST include a clear explanation of applied adjustments (or unresolved constraints) in optimized outputs.
- **FR-011**: System MUST fail gracefully with actionable error messages when required inputs are missing or invalid.
- **FR-012**: System MUST keep optional tool augmentation (for example, MCP-powered lookups) behind an explicit opt-in path and MUST NOT require it for core flow success.

### Key Entities *(include if feature involves data)*

- **TripRequest**: User-provided planning intent with destination, month, budget, and optional preferences.
- **ResearchBrief**: Destination context including attractions, weather expectations, events, and local tips.
- **DraftItinerary**: Day-by-day schedule with time slots and activity notes.
- **BudgetEstimate**: Cost model covering transport, lodging, meals, and activities.
- **TripProposal**: Fan-in aggregate that combines research, itinerary, and budget.
- **ValidationResult**: Constraint checks indicating budget fit, conflict presence, and rationale.
- **OptimizedProposal**: Revised proposal with substitutions/reordering and explicit trade-offs.
- **TripBrief**: Final markdown-ready package and output file metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successful runs produce a markdown file with all required sections: itinerary, budget breakdown, and packing/prep tips.
- **SC-002**: At least 95% of valid-input runs complete without manual intervention.
- **SC-003**: 100% of over-budget or conflict-containing draft plans trigger the optimization route.
- **SC-004**: 100% of within-budget and conflict-free draft plans bypass optimization and go directly to finalization.
- **SC-005**: A presenter can execute one demonstration run in each backend mode and produce comparable trip briefs from the same prompt.

## Assumptions

- The trip scope is a single traveler and fixed to 3 days in v1.
- Currency is treated as USD for input and output examples.
- Cost estimates are directional planning guidance, not booking guarantees.
- Output language is English for v1.
- Network-dependent enrichments may vary, but the system still returns a coherent brief without optional tool augmentation.
