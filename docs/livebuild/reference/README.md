# Reference implementation

The finished spine. You re-derive this live; this copy is the answer key and the fallback.

```bash
source ../../../.venv/bin/activate
cp .env.example .env       # or reuse the repo's
python3 deploy_agents.py                   # 12s
PYTHONPATH=src python3 -m tripspine        # 38s
```

| File | Lines | What it is |
|---|---|---|
| `deploy_agents.py` | 111 | three PromptAgents → Foundry Agent Service, with their tools |
| `src/tripspine/workflow.py` | 120 | agent_reference calls, concurrent fan-out, conditional edge |
| `src/tripspine/__main__.py` | 52 | parse the prompt, run, write the brief |

Verified against `trip-planner-prod`. The three agents are deployed and at v2.

The stage script is [`../README.md`](../README.md).
