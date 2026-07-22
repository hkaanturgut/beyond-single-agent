# Malta Microsoft AI User Group — Deep Dive Notes

## Focus for this talk

Use the trip-planner scenario to tell a **platform + production** story:

1. Workflow topology (concurrent fan-out + conditional routing)
2. Azure AI Foundry backend path
3. YAML workflow portability
4. Optional MCP extension strategy
5. Observability and deployment controls

## Demo — run it now

### Option A: Demo mode (no Azure needed)

```bash
python -m trip_planner "Plan my 3-day trip to Valletta in April with budget \$2200"
```

### Option B: Azure AI Foundry (production path)

```bash
# 1. Deploy infra
az deployment group create \
  --resource-group rg-trip-planner-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.bicepparam

# 2. Set env vars
export TRIP_BACKEND=foundry
export FOUNDRY_PROJECT_ENDPOINT=<output from deployment>

# 3. Authenticate
az login

# 4. Run
python -m trip_planner "Plan my 3-day trip to Valletta in April with budget \$2200"
```

## Malta-specific code walkthrough

| Area | File | What to highlight |
|---|---|---|
| Foundry backend | `src/trip_planner/backends/foundry.py` | `AIProjectClient` + `DefaultAzureCredential` |
| Backend factory | `src/trip_planner/backends/__init__.py` | `create_backend(cfg)` — env-var driven |
| YAML pipeline | `workflows/trip-planner-pipeline.yaml` | Human-readable workflow descriptor |
| Infra (Bicep) | `infra/main.bicep` + `infra/modules/foundry.bicep` | Foundry Hub + Project deployment |
| Telemetry | `src/trip_planner/workflow/telemetry.py` | `stage_span` — structured timing per stage |
| MCP bridge | `src/trip_planner/tools/mcp_bridge.py` | Opt-in extension pattern |

## Malta-specific talking points

- Why **conditional routing** is the operational hinge (optimize vs finalize).
- Why **backend adapters** de-risk environment drift between local and production.
- Why **output artifacts** (`trip-<destination>-<timestamp>.md`) are audit-friendly.
- Why MCP integration is optional-by-default for reliability during live demos.
- How **Bicep** deploys the Foundry Hub + Project in a reproducible, team-shareable way.

## One-line close

**The win is not more prompts — it is a workflow the team can reason about, operate, and ship.**
