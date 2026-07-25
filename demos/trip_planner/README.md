# Trip Planner Demo — Sample Invocations

This project runs entirely on **Azure AI Foundry**. Both backends call the same
Foundry project — there is no offline/demo mode.

## Setup

```bash
cd <repo-root>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # set FOUNDRY_PROJECT_ENDPOINT, then `az login`
```

## Run with hosted multi-agent workflow (default)

Each specialist call is routed to its hosted PromptAgent in Foundry Agent
Service. Run `scripts/deploy_agents.py` once first to register the agents.

```bash
# Scenario A — finalize route (budget comfortable)
TRIP_BACKEND=foundry \
  FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project> \
  python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"

# Scenario B — optimizer route (tight budget triggers optimization)
TRIP_BACKEND=foundry \
  FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project> \
  python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$600"
```

## Run with direct Foundry model inference (no hosted agents)

Uses the same Foundry model deployment via chat completions.

```bash
TRIP_BACKEND=foundry_models \
  FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project> \
  python -m trip_planner "Plan my 3-day trip to Kyoto in October with budget \$1800"
```

## Run tests

```bash
pytest tests/ -v
pytest tests/unit/ -v        # unit only (fast, no I/O)
pytest tests/integration/ -v
pytest tests/contract/ -v
```

## Output files

All generated briefs are written to `output/trip-<destination>-<timestamp>.md`.
