# Beyond a Single Agent — Trip Planner Demo

This repository has pivoted to a **spec-first** build of a Python multi-agent trip planner for two talks:

- [Python Toronto](talks/python-toronto/README.md): concise code walkthrough focused on concurrent + conditional workflow patterns.
- [Malta Microsoft AI User Group](talks/malta/README.md): deeper platform narrative focused on Azure AI Foundry, YAML workflows, MCP tools, and production concerns.

## Scenario

User prompt:

> Plan my 3-day trip to `<destination>` in `<month>` with budget `$<amount>`

Target workflow:

1. Fan-out specialists run concurrently (`ResearcherAgent`, `PlannerAgent`, `BudgetAgent`).
2. Fan-in aggregator merges outputs.
3. Conditional route:
   - If over budget or schedule conflicts -> `OptimizerAgent`
   - Else -> `FinalizerAgent`
4. Save polished markdown brief to `output/trip-<destination>-<timestamp>.md`.

## Spec Kit workflow (completed)

This repo now includes GitHub Spec Kit scaffolding and generated planning artifacts.

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --integration copilot --force
```

Primary artifacts:

| Artifact | Path |
| --- | --- |
| Specification (WHAT/WHY) | [`specs/001-trip-planner-demo/spec.md`](specs/001-trip-planner-demo/spec.md) |
| Implementation plan (HOW) | [`specs/001-trip-planner-demo/plan.md`](specs/001-trip-planner-demo/plan.md) |
| Ordered task breakdown | [`specs/001-trip-planner-demo/tasks.md`](specs/001-trip-planner-demo/tasks.md) |
| Supporting design docs | [`specs/001-trip-planner-demo/`](specs/001-trip-planner-demo/) |

## Current status

- ✅ Spec, plan, and tasks are complete.
- ✅ Previous placeholder scaffold is archived at [`_archive/previous-multi-agent-scaffold-20260722/`](./_archive/previous-multi-agent-scaffold-20260722/).
- 🚧 Agent implementation intentionally not started yet (next step is `/speckit.implement`).

## Repository map (current)

| Path | Purpose |
| --- | --- |
| `.specify/` | Spec Kit templates, scripts, and workflow metadata |
| `.github/agents/` + `.github/prompts/` | Slash-command agent/prompt definitions |
| `specs/001-trip-planner-demo/` | Scenario spec, plan, tasks, contracts, quickstart |
| `talks/malta/` | Malta-focused narrative |
| `talks/python-toronto/` | Python Toronto-focused narrative |
| `_archive/` | Previous placeholder implementation kept for reference |

## Local setup (for planning review)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Implementation and runtime commands will be added after `/speckit.implement`.
