# Implementation Plan: Beyond a Single Agent — Trip Planner Demo

**Branch**: `001-trip-planner-demo` | **Date**: 2026-07-22 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `/specs/001-trip-planner-demo/spec.md`

## Summary

Build a Python workflow app that turns a natural-language trip request into a polished markdown trip brief. The flow follows two explicit orchestration patterns: (1) concurrent fan-out/fan-in across specialist agents and (2) conditional routing to either optimization or finalization. The same architecture must run with two interchangeable model backends (local-friendly and production-oriented) and support talk narratives for Python Toronto and Malta without branching the core app.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `agent-framework` for workflow graph construction (`WorkflowBuilder`, `ConcurrentBuilder`, conditional edge groups)
- `azure-ai-projects` + `azure-identity` for production Foundry-backed client flows
- `python-dotenv` for environment configuration
- `pydantic` for strongly typed workflow payload contracts
- `PyYAML` for Malta-oriented workflow YAML artifacts

**Storage**:
- Local filesystem output in `output/`
- Optional lightweight local cache/log files under `.runtime/` (non-source artifacts)

**Testing**:
- `pytest` for unit/integration tests
- Contract-style schema tests for agent payload handoffs

**Target Platform**:
- macOS/Linux developer machines (CLI runs)
- CI execution in GitHub Actions

**Project Type**: Single Python CLI application with orchestrated workflow components

**Performance Goals**:
- Produce a completed trip brief in under 30 seconds for typical requests in non-production mode
- Complete one deterministic talk demo run in under 2 minutes end-to-end (including startup)

**Constraints**:
- No hardcoded secrets; all credentials via environment variables
- Workflow behavior must be explainable stage-by-stage for live demos
- Output artifact naming must be safe and deterministic
- Core flow must run without optional MCP integration

**Scale/Scope**:
- Single-user, single-request interactive runs
- 3-day trip planning only in v1
- Demo-oriented reliability over high-throughput operation

## Architecture & Agent Contracts

### Workflow stages

1. **Request Intake**
   - Parse destination, month, and budget from user prompt.
   - Validate required fields and normalize values.

2. **Fan-out (ConcurrentBuilder)**
   - `ResearcherAgent`: attractions, weather, events, cultural tips.
   - `PlannerAgent`: day-by-day itinerary with time slots.
   - `BudgetAgent`: flights, lodging, meals, activities estimate.

3. **Fan-in Aggregator**
   - Combines all specialist outputs into `TripProposal`.
   - Produces derived metrics used for conditional routing.

4. **Conditional Routing**
   - If `estimated_cost > budget` OR conflicts detected: route to `OptimizerAgent`.
   - Else: route to `FinalizerAgent`.

5. **Final Output**
   - Markdown brief with itinerary, budget table, optimization notes/trade-offs, and packing/prep tips.
   - Save to `output/trip-<destination>-<timestamp>.md`.

### Payload contracts (high level)

- `TripRequest` -> shared input for all agents
- `ResearchOutput`, `PlanOutput`, `BudgetOutput` -> specialist outputs
- `TripProposal` -> aggregation result
- `ValidationResult` -> cost/constraint evaluation
- `OptimizedProposal` -> optional revised proposal
- `FinalTripBrief` -> markdown + file metadata

### Backend strategy

- Backend selected via env var (for example `TRIP_BACKEND=github_models|foundry`).
- A backend adapter interface provides a consistent `generate(prompt, context)` method.
- Foundry adapter uses `AIProjectClient` + `DefaultAzureCredential`.
- Local-friendly adapter uses GitHub Models-compatible client configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Current `.specify/memory/constitution.md` is an uncustomized template with no enforceable project-specific gates yet. Temporary planning gates applied for this feature:

1. **No secret leakage**: Pass (env-var-only credential policy in scope).
2. **Workflow clarity**: Pass (explicit staged architecture and routing rules documented).
3. **No premature implementation**: Pass (spec/plan/tasks only in this phase).

Re-check after implementation starts:
- Ensure all generated artifacts and examples remain secret-free.
- Ensure routing decisions remain observable in logs/trace output.

## Project Structure

### Documentation (this feature)

```text
specs/001-trip-planner-demo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── trip-workflow-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── trip_planner/
    ├── __init__.py
    ├── cli.py
    ├── config.py
    ├── models/
    │   ├── request.py
    │   ├── proposal.py
    │   └── validation.py
    ├── backends/
    │   ├── base.py
    │   ├── github_models.py
    │   └── foundry.py
    ├── agents/
    │   ├── researcher.py
    │   ├── planner.py
    │   ├── budget.py
    │   ├── optimizer.py
    │   └── finalizer.py
    ├── workflow/
    │   ├── builder.py
    │   ├── aggregator.py
    │   └── router.py
    ├── output/
    │   └── writer.py
    └── tools/
        └── mcp_bridge.py

tests/
├── unit/
├── integration/
└── contract/

output/
_archive/
```

**Structure Decision**: Single-project Python CLI layout centered on `src/trip_planner`. This keeps implementation shallow for the Python talk while preserving explicit layers (models, agents, workflow, backends) needed for Malta’s production narrative.

## Complexity Tracking

No constitution violations requiring exception handling at planning time.
