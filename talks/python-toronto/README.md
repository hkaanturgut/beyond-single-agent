# Beyond a Single Agent: Trip Planner Workflow (Python Toronto Notes)

## Focus for this talk

Tell a **Python-first** story using one concrete scenario:

> Plan my 3-day trip to `<destination>` in `<month>` with budget `$<amount>`

Core teaching points:

- Concurrent decomposition (research/planning/budget in parallel)
- Fan-in aggregation
- Conditional branch (optimize vs finalize)
- Clean backend swap (local-friendly vs Foundry)

## Demo — run it now

```bash
# No credentials needed — runs in demo mode
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"

# With GitHub token — uses real GitHub Models API
TRIP_BACKEND=github_models GITHUB_TOKEN=<token> \
  python -m trip_planner "Plan my 3-day trip to Kyoto in October with budget \$1800"
```

## Talk flow — code walkthrough

| Step | File | What to highlight |
|---|---|---|
| 1 | `src/trip_planner/models/request.py` | `parse_trip_request` — regex-based NL parser |
| 2 | `src/trip_planner/workflow/builder.py` | `WorkflowBuilder`, `ConcurrentBuilder`, `add_multi_selection_edge_group` |
| 3 | `src/trip_planner/agents/` | Five agents, each focused on one concern |
| 4 | `src/trip_planner/workflow/aggregator.py` | Fan-in — all parts combined into `TripProposal` |
| 5 | `src/trip_planner/workflow/router.py` | Routing decision — budget + conflict checks |
| 6 | `src/trip_planner/agents/finalizer.py` | Markdown rendering |
| 7 | `src/trip_planner/output/writer.py` | Safe file naming + timestamp |

## Two demo scenarios

### Scenario A — finalize route (budget-comfortable)

```bash
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$2600"
```

### Scenario B — optimizer route (tight budget)

```bash
python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget \$600"
```

Watch the log line: `route decision: optimize (over_budget=True ...)`

## Tests

```bash
pytest tests/ -v
```

## Key message

The win is not "more agents"; the win is **explicit workflow boundaries** that make Python code easier to build, test, and reason about.
