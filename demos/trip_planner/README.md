# Trip Planner Demo — Sample Invocations

## Quick start (no credentials needed)

```bash
cd <repo-root>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # TRIP_BACKEND=demo by default
```

## Run the two core scenarios

```bash
# Scenario A — finalize route (budget comfortable)
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"

# Scenario B — optimizer route (tight budget triggers optimization)
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$600"
```

## Run with GitHub Models (local-friendly live mode)

```bash
TRIP_BACKEND=github_models GITHUB_TOKEN=<your-token> \
  python -m trip_planner "Plan my 3-day trip to Kyoto in October with budget \$1800"
```

## Run with Azure AI Foundry (production mode)

```bash
# Requires: FOUNDRY_PROJECT_ENDPOINT and az login (or service principal)
TRIP_BACKEND=foundry \
  FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project> \
  python -m trip_planner "Plan my 3-day trip to Valletta in April with budget \$2200"
```

## Run tests

```bash
pytest tests/ -v
pytest tests/unit/ -v       # unit only (fast, no I/O)
pytest tests/integration/ -v
pytest tests/contract/ -v
```

## Output files

All generated briefs are written to `output/trip-<destination>-<timestamp>.md`.
