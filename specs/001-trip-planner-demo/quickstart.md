# Quickstart: Beyond a Single Agent — Trip Planner Demo

This guide is the step-by-step runbook for running the demo.

## 1) Choose the infra strategy

- **Default choice for this repo**: **Bicep** for Azure resources.
- **Why**: Microsoft Foundry docs explicitly call out Bicep templates for Foundry resources and project connections, and the official Foundry samples are Bicep-first.
- **Agents/workflows**: built in Python with **Microsoft Agent Framework** patterns. Agents are code; infra is the Azure resource layer around them.
- **Terraform**: fine if your org already standardizes on it, but not the default for this demo.

## 2) Provision the Azure side (optional — only for Foundry backend)

Deploy with Bicep:

```bash
az group create --name rg-trip-planner-dev --location eastus2

az deployment group create \
  --resource-group rg-trip-planner-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.bicepparam
```

Copy the `foundryProjectEndpoint` output value — you will need it for step 3.

See [`infra/README.md`](../../infra/README.md) for full deployment notes.

## 3) Prepare local dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Select backend mode in `.env`:
- `TRIP_BACKEND=demo` → no credentials needed (default)
- `TRIP_BACKEND=github_models` → set `GITHUB_TOKEN=<your token>`
- `TRIP_BACKEND=foundry` → set `FOUNDRY_PROJECT_ENDPOINT=<output from step 2>` and run `az login`

## 4) Run the trip planner

```bash
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"
```

The workflow will:

1. Fan out to ResearcherAgent, PlannerAgent, and BudgetAgent concurrently
2. Aggregate the results
3. Route to finalize or optimize
4. Save a markdown brief under `output/`

## 5) Try the two branches

### Finalize route (budget-comfortable)

```bash
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"
```

Look for: `route decision: finalize (over_budget=False, conflicts=False)`

### Optimizer route (tight budget)

```bash
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$600"
```

Look for: `route decision: optimize (over_budget=True ...)`

## 6) Validation scenarios

### Scenario 1: Happy path (finalizer route)

- Request: `Plan my 3-day trip to Lisbon in May with budget $2600`
- Expected:
  - workflow fan-out and fan-in complete
  - route decision is `finalize`
  - output file contains itinerary, budget breakdown, and packing/prep tips

### Scenario 2: Over-budget path (optimizer route)

- Request: `Plan my 3-day trip to Lisbon in May with budget $600`
- Expected:
  - route decision is `optimize`
  - revised proposal produced before final output
  - output includes optimization notes/trade-offs

### Scenario 3: Conflict-triggered optimization

- Use test fixtures that intentionally create overlapping itinerary slots.
- Expected:
  - `has_schedule_conflicts = true`
  - route decision is `optimize`
  - final output includes conflict-resolution notes

### Scenario 4: Invalid input handling

- Submit malformed request (missing budget).
- Expected:
  - validation error message with actionable correction guidance
  - no output markdown file created

### Scenario 5: Backend parity check

- Run the same valid request in backend mode A and backend mode B.
- Expected:
  - both runs complete
  - both produce markdown briefs with the same required sections

## 7) Run tests

```bash
pytest tests/ -v
```

Expected: 50 tests pass.
