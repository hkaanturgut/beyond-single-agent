# Malta Microsoft AI User Group

## Talk angle

This version of the demo is the **platform and operations** story:

- show the orchestrator as a system, not just a prompt,
- connect the Python code to a YAML workflow,
- explain why MCP tools improve composability,
- end on deployment and observability instead of just "look, it works."

## Recommended live path

1. Run `python demos/single_agent_fail/demo.py`.
2. Run `python demos/multi_agent_win/demo.py --audience malta`.
3. Open [`workflows/pipeline.yaml`](../../workflows/pipeline.yaml).
4. Open [`tools/mcp_tools.py`](../../tools/mcp_tools.py).
5. Finish in [`agents/orchestrator.py`](../../agents/orchestrator.py) to show the live Foundry hook.

## Files to call out

- [`workflows/pipeline.yaml`](../../workflows/pipeline.yaml) — orchestration as code
- [`tools/mcp_tools.py`](../../tools/mcp_tools.py) — stable tool contracts
- [`agents/orchestrator.py`](../../agents/orchestrator.py) — routing and live Foundry integration
- [`README.md`](../../README.md) — the shared architecture story

## Production callouts

- `DefaultAzureCredential` keeps the sample aligned with managed identity and service-principal deployment models.
- The YAML template includes approval gates, tracing, evaluation, and canary rollback.
- MCP-style tools reduce blast radius because retrieval concerns stay isolated from narrative generation.

## One-line close

**The shift is from "one clever agent" to "a workflow the team can review, observe, and deploy."**

