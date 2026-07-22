# Beyond a Single Agent — Trip Planner Demo

This repository is a **spec-first** Python multi-agent trip planner built for two talks:

- [Python Toronto](talks/python-toronto/README.md): concise code walkthrough focused on concurrent + conditional workflow patterns.
- [Malta Microsoft AI User Group](talks/malta/README.md): deeper platform narrative focused on Azure AI Foundry, Bicep infra, YAML workflows, MCP tools, and production concerns.

## Scenario

User prompt:

> Plan my 3-day trip to `<destination>` in `<month>` with budget `$<amount>`

Workflow:

1. **Fan-out** — `ResearcherAgent`, `PlannerAgent`, `BudgetAgent` run concurrently (`ConcurrentBuilder`).
2. **Fan-in** — aggregator merges outputs into one `TripProposal`.
3. **Conditional route** (`add_multi_selection_edge_group`):
   - If over budget or schedule conflicts → `OptimizerAgent`
   - Else → `FinalizerAgent`
4. **Output** — polished markdown brief saved to `output/trip-<destination>-<timestamp>.md`.

## Quick start

```bash
# Clone and set up
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Demo mode — no credentials needed
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"

# With GitHub token (live LLM responses)
TRIP_BACKEND=github_models GITHUB_TOKEN=<token> \
  python -m trip_planner "Plan my 3-day trip to Kyoto in October with budget \$1800"
```

## Runtime backends

| `TRIP_BACKEND` | Description | Requires |
|---|---|---|
| `demo` (default) | Deterministic template responses — no external calls | Nothing |
| `github_models` | GitHub Models OpenAI-compatible API | `GITHUB_TOKEN` |
| `foundry` | Azure AI Foundry via `AIProjectClient` | `FOUNDRY_PROJECT_ENDPOINT` + Azure auth |

## Azure deployment via GitHub Actions

The `Deploy Azure infrastructure` workflow provisions the Azure side of the demo:

- Storage account
- Log Analytics workspace
- Application Insights
- Foundry hub
- Foundry project
- Azure AI Services account
- `gpt-4.1-mini` model deployment
- Hub-to-model connection

One-time setup:

1. Create a Microsoft Entra application or user-assigned managed identity with a federated credential for this repository.
2. Grant it `Contributor` on the target resource group.
3. Add these GitHub secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
4. Run the workflow from the **Actions** tab and copy the `foundryProjectEndpoint` output into `.env`.

## Repository map

| Path | Purpose |
|---|---|
| `src/trip_planner/` | Main Python package — agents, workflow, backends, models |
| `src/trip_planner/workflow/builder.py` | `WorkflowBuilder`, `ConcurrentBuilder`, routing |
| `src/trip_planner/agents/` | Five specialist agents |
| `src/trip_planner/backends/` | Backend adapters + factory |
| `infra/` | Bicep templates for Foundry hub, project, AI Services model, and observability |
| `tests/` | Unit, integration, and contract tests |
| `output/` | Generated trip-brief markdown files (git-ignored) |
| `workflows/trip-planner-pipeline.yaml` | Human-readable YAML workflow descriptor |
| `specs/001-trip-planner-demo/` | Spec, plan, tasks, contracts, quickstart |
| `talks/malta/` | Malta-focused talk narrative |
| `talks/python-toronto/` | Python Toronto-focused talk narrative |
| `demos/trip_planner/` | Sample invocations |
| `.specify/` | Spec Kit templates, scripts, and workflow metadata |
| `_archive/` | Previous placeholder implementation kept for reference |

## Tests

```bash
pytest tests/ -v
```

## Spec Kit workflow (completed)

This repo was built spec-first using GitHub Spec Kit.

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --integration copilot --force
```

| Artifact | Path |
|---|---|
| Specification (WHAT/WHY) | [`specs/001-trip-planner-demo/spec.md`](specs/001-trip-planner-demo/spec.md) |
| Implementation plan (HOW) | [`specs/001-trip-planner-demo/plan.md`](specs/001-trip-planner-demo/plan.md) |
| Ordered task breakdown | [`specs/001-trip-planner-demo/tasks.md`](specs/001-trip-planner-demo/tasks.md) |
| Quickstart / runbook | [`specs/001-trip-planner-demo/quickstart.md`](specs/001-trip-planner-demo/quickstart.md) |

## Operational notes

- **No secrets in source control** — all credentials are read from environment variables.
- **Route decisions are logged** — watch for `route decision: optimize/finalize` in stdout.
- **Non-fatal errors are tolerated** — a backend timeout does not crash the workflow;
  affected specialist outputs fall back to safe defaults.
- **Output files are timestamped** — each run produces a new file; old files are not overwritten.
- **Bicep infra** — see [`infra/README.md`](infra/README.md) for production deployment instructions.
