# Beyond a Single Agent: Trip Planner Workflow (Python Toronto Notes)

## Focus for this talk

Tell a **Python-first** story using one concrete scenario:

> Plan my 3-day trip to `<destination>` in `<month>` with budget `$<amount>`

Core teaching points:

- Concurrent decomposition (research/planning/budget in parallel)
- Fan-in aggregation
- Conditional branch (optimize vs finalize)
- Clean backend swap (local-friendly vs Foundry)

## Current repo phase

This branch is intentionally pre-implementation. Use these files for walkthrough:

1. [`specs/001-trip-planner-demo/spec.md`](../../specs/001-trip-planner-demo/spec.md)
2. [`specs/001-trip-planner-demo/plan.md`](../../specs/001-trip-planner-demo/plan.md)
3. [`specs/001-trip-planner-demo/tasks.md`](../../specs/001-trip-planner-demo/tasks.md)
4. [`specs/001-trip-planner-demo/data-model.md`](../../specs/001-trip-planner-demo/data-model.md)

## Timeboxed flow

### 5 minutes

- Show spec -> plan -> tasks progression
- Emphasize why single-agent prompting hides control-flow decisions

### 10 minutes

- Zoom in on workflow stages in `plan.md`
- Show contract schema in `contracts/trip-workflow-contract.md`

### 15 minutes

- Walk task ordering and MVP slice (US1) from `tasks.md`
- Explain how concurrent + conditional patterns map to `agent-framework` primitives

## Key message

The win is not "more agents"; the win is **explicit workflow boundaries** that make Python code easier to build, test, and reason about.
