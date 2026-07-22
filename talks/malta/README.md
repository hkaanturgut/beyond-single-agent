# Malta Microsoft AI User Group — Deep Dive Notes

## Focus for this talk

Use the trip-planner scenario to tell a **platform + production** story:

1. Workflow topology (concurrent fan-out + conditional routing)
2. Azure AI Foundry backend path
3. YAML workflow portability
4. Optional MCP extension strategy
5. Observability and deployment controls

## Current repo phase

This repo is intentionally in spec-first mode (no new implementation yet). Walk the design artifacts:

1. [`specs/001-trip-planner-demo/spec.md`](../../specs/001-trip-planner-demo/spec.md)
2. [`specs/001-trip-planner-demo/plan.md`](../../specs/001-trip-planner-demo/plan.md)
3. [`specs/001-trip-planner-demo/tasks.md`](../../specs/001-trip-planner-demo/tasks.md)
4. [`specs/001-trip-planner-demo/contracts/trip-workflow-contract.md`](../../specs/001-trip-planner-demo/contracts/trip-workflow-contract.md)

## Malta-specific talking points

- Why **conditional routing** is the operational hinge (optimize vs finalize).
- Why **backend adapters** de-risk environment drift between local and production.
- Why **output artifacts** (`trip-<destination>-<timestamp>.md`) are audit-friendly.
- Why MCP integration is optional-by-default for reliability during live demos.

## Bridge to implementation

When implementation starts, prioritize these items from `tasks.md`:

- Foundry adapter wiring
- Workflow YAML for review/promotion
- Telemetry and route-decision traceability
- Production hardening checks (secrets, retries, rollout path)

## One-line close

**The win is not more prompts — it is a workflow the team can reason about, operate, and ship.**
