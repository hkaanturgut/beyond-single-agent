# Research Notes: Beyond a Single Agent — Trip Planner Demo

## Decision 1: Use explicit concurrent + conditional workflow structure

- **Decision**: Model the workflow as fan-out (research/planning/budget), fan-in aggregation, and conditional routing to optimize/finalize.
- **Rationale**: This directly demonstrates the two pedagogical patterns required for both talks: concurrent decomposition and conditional control flow.
- **Alternatives considered**:
  - Single sequential chain: rejected because it does not showcase concurrent decomposition.
  - Single-agent prompt orchestration: rejected because branching and retry behavior become opaque.

## Decision 2: Support two backend modes behind one adapter contract

- **Decision**: Define a backend adapter interface and select implementation by environment variable.
- **Rationale**: One workflow implementation can be reused for local demo mode and Foundry production mode without changing orchestration logic.
- **Alternatives considered**:
  - Hardcode one backend: rejected because it breaks the dual-talk objective.
  - Duplicate workflow per backend: rejected due to maintenance overhead and narrative divergence.

## Decision 3: Keep output as markdown artifact

- **Decision**: Emit markdown to `output/trip-<destination>-<timestamp>.md`.
- **Rationale**: Markdown is demo-friendly, reviewable, and easy to diff; it also maps cleanly to “final brief” user value.
- **Alternatives considered**:
  - JSON-only output: rejected as less presenter-friendly.
  - Database persistence: rejected as unnecessary for v1 demo scope.

## Decision 4: Make MCP integration optional

- **Decision**: Treat MCP-based enrichment as opt-in extension work.
- **Rationale**: Keeps core scenario reliable and runnable even when external tools are unavailable.
- **Alternatives considered**:
  - Mandatory MCP dependency: rejected due to setup fragility during short live demos.

