# Tasks: Beyond a Single Agent — Trip Planner Demo

**Input**: Design documents from `/specs/001-trip-planner-demo/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include unit, integration, and contract tests because routing correctness is a core requirement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project structure and baseline configuration

- [X] T001 Create package skeleton under `src/trip_planner/` with subpackages `agents/`, `backends/`, `models/`, `workflow/`, `output/`, and `tools/`
- [X] T002 Update `requirements.txt` with planned dependencies (`agent-framework`, `azure-ai-projects`, `azure-identity`, `python-dotenv`, `pydantic`, `PyYAML`)
- [X] T003 Update `.env.example` with backend toggle and Foundry/GitHub Models configuration keys
- [X] T004 [P] Update `.gitignore` to include runtime artifacts in `output/` and `.runtime/` while preserving committed directory placeholders
- [X] T005 [P] Create testing scaffold directories `tests/unit/`, `tests/integration/`, and `tests/contract/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core contracts and infrastructure required by all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement typed request/proposal/validation models in `src/trip_planner/models/request.py`, `src/trip_planner/models/proposal.py`, and `src/trip_planner/models/validation.py`
- [X] T007 Implement configuration loader and backend selection in `src/trip_planner/config.py`
- [X] T008 Implement backend interface contract in `src/trip_planner/backends/base.py`
- [X] T009 [P] Implement GitHub Models backend adapter in `src/trip_planner/backends/github_models.py`
- [X] T010 [P] Implement Azure AI Foundry backend adapter in `src/trip_planner/backends/foundry.py`
- [X] T011 Implement backend factory in `src/trip_planner/backends/__init__.py`
- [X] T012 Implement safe markdown writer (filename normalization + timestamping) in `src/trip_planner/output/writer.py`
- [X] T013 [P] Implement shared workflow state object definitions in `src/trip_planner/workflow/state.py`
- [X] T014 Implement baseline logging/tracing utility in `src/trip_planner/workflow/telemetry.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate initial trip brief (Priority: P1) 🎯 MVP

**Goal**: Produce a complete trip brief from one valid request using fan-out + fan-in

**Independent Test**: Run one valid request and verify markdown output with required sections is saved to `output/`

### Tests for User Story 1

- [X] T015 [P] [US1] Add parser and request validation tests in `tests/unit/test_request_parser.py`
- [X] T016 [P] [US1] Add fan-out/fan-in workflow integration test in `tests/integration/test_fanout_fanin.py`
- [X] T017 [P] [US1] Add final markdown contract test in `tests/contract/test_trip_brief_sections.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement `ResearcherAgent` in `src/trip_planner/agents/researcher.py`
- [X] T019 [P] [US1] Implement `PlannerAgent` in `src/trip_planner/agents/planner.py`
- [X] T020 [P] [US1] Implement `BudgetAgent` in `src/trip_planner/agents/budget.py`
- [X] T021 [US1] Implement fan-in aggregator in `src/trip_planner/workflow/aggregator.py`
- [X] T022 [US1] Build concurrent workflow stages with `ConcurrentBuilder` in `src/trip_planner/workflow/builder.py`
- [X] T023 [US1] Implement `FinalizerAgent` markdown formatter in `src/trip_planner/agents/finalizer.py`
- [X] T024 [US1] Wire CLI entry point and prompt intake in `src/trip_planner/cli.py`
- [X] T025 [US1] Persist finalized brief through output writer integration in `src/trip_planner/workflow/runner.py`

**Checkpoint**: User Story 1 is fully functional and demoable as MVP

---

## Phase 4: User Story 2 - Optimize over-budget/conflicting plans (Priority: P2)

**Goal**: Route invalid proposals through optimizer and return revised output

**Independent Test**: Submit over-budget and conflict fixtures and verify routing + optimization notes

### Tests for User Story 2

- [X] T026 [P] [US2] Add budget-threshold routing tests in `tests/unit/test_budget_routing.py`
- [X] T027 [P] [US2] Add conflict-detection routing tests in `tests/unit/test_conflict_routing.py`
- [X] T028 [P] [US2] Add optimizer path integration test in `tests/integration/test_optimizer_path.py`

### Implementation for User Story 2

- [X] T029 [US2] Implement route decision logic in `src/trip_planner/workflow/router.py`
- [X] T030 [US2] Implement `OptimizerAgent` in `src/trip_planner/agents/optimizer.py`
- [X] T031 [US2] Integrate conditional branching with `add_multi_selection_edge_group` in `src/trip_planner/workflow/builder.py`
- [X] T032 [US2] Add optimization notes/trade-off rendering in `src/trip_planner/agents/finalizer.py`
- [X] T033 [US2] Add fallback behavior for unresolved constraints in `src/trip_planner/workflow/runner.py`

**Checkpoint**: User Stories 1 and 2 both work independently and together

---

## Phase 5: User Story 3 - Backend parity for both talks (Priority: P3)

**Goal**: Run same workflow with two backend modes without changing core orchestration logic

**Independent Test**: Execute same request in both modes and compare required output sections

### Tests for User Story 3

- [X] T034 [P] [US3] Add backend adapter contract tests in `tests/contract/test_backend_adapter_contract.py`
- [X] T035 [P] [US3] Add dual-backend parity integration test in `tests/integration/test_backend_parity.py`

### Implementation for User Story 3

- [X] T036 [US3] Add backend mode switch handling in `src/trip_planner/config.py` and `src/trip_planner/cli.py`
- [X] T037 [US3] Add Foundry-mode runtime wiring in `src/trip_planner/backends/foundry.py` and `src/trip_planner/workflow/runner.py`
- [X] T038 [US3] Add GitHub Models runtime wiring in `src/trip_planner/backends/github_models.py` and `src/trip_planner/workflow/runner.py`
- [X] T039 [US3] Add talk-oriented sample invocations in `demos/trip_planner/README.md`

**Checkpoint**: All three user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish observability, optional extensions, and final documentation polish

- [X] T040 [P] Add optional MCP bridge scaffold behind config flag in `src/trip_planner/tools/mcp_bridge.py`
- [X] T041 Add workflow YAML mapping for Malta deep dive in `workflows/trip-planner-pipeline.yaml`
- [X] T042 [P] Update talk guides in `talks/python-toronto/README.md` and `talks/malta/README.md`
- [X] T043 Add operational notes for observability and production rollout in `README.md`
- [X] T044 Run quickstart validation and capture expected outputs in `specs/001-trip-planner-demo/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories
- **User Stories (Phases 3-5)**: Depend on Foundational completion
  - US1 should be delivered first for MVP
  - US2 and US3 can proceed after US1 baseline runner exists
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on foundational work
- **US2 (P2)**: Depends on US1 workflow runner + aggregator
- **US3 (P3)**: Depends on foundational adapters and US1 runner wiring

### Within Each User Story

- Write tests first
- Implement agents/adapters
- Wire orchestration and routing
- Validate with integration tests
- Finalize markdown/output behavior

### Parallel Opportunities

- Setup tasks T004-T005 can run in parallel
- Foundational adapter tasks T009-T010 can run in parallel
- US1 specialist agent tasks T018-T020 can run in parallel
- US2 routing tests T026-T028 can run in parallel
- US3 backend parity tests T034-T035 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Parallel specialist implementation
Task: T018 [US1] Implement ResearcherAgent in src/trip_planner/agents/researcher.py
Task: T019 [US1] Implement PlannerAgent in src/trip_planner/agents/planner.py
Task: T020 [US1] Implement BudgetAgent in src/trip_planner/agents/budget.py

# Parallel test authoring
Task: T015 [US1] tests/unit/test_request_parser.py
Task: T016 [US1] tests/integration/test_fanout_fanin.py
Task: T017 [US1] tests/contract/test_trip_brief_sections.py
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 + Phase 2.
2. Deliver US1 fully (Phase 3).
3. Validate output artifact generation and markdown completeness.

### Incremental Delivery

1. Add US2 for optimizer routing.
2. Add US3 for backend parity.
3. Finish with polish and optional MCP extension support.

### Parallel Team Strategy

1. One developer owns foundational contracts/backends.
2. One developer owns specialist agents + aggregator.
3. One developer owns routing + optimizer + integration tests.

