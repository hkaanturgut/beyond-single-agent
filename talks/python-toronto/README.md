# Beyond a Single Agent: Building Multi-Agent Workflows in Python with Microsoft Agent Framework

## Talk angle

This version of the demo is the **Python developer** story:

- keep the classes small,
- make responsibilities obvious,
- show that multi-agent can be regular Python code,
- connect the implementation back to Azure AI Foundry only after the audience understands the core pattern.

## Timeboxed versions

### 5 minutes

- Run `single_agent_fail/demo.py`
- Run `multi_agent_win/demo.py --audience python-toronto`
- Open `agents/orchestrator.py`

### 10 minutes

- Add `research_agent.py` and `summarizer_agent.py`
- Show the tool interface in `tools/mcp_tools.py`

### 20 minutes

- Add `workflows/pipeline.yaml`
- Explain how the same Python code maps cleanly to a Foundry-hosted setup

## Files to open

- [`agents/orchestrator.py`](../../agents/orchestrator.py)
- [`agents/domain_agents/research_agent.py`](../../agents/domain_agents/research_agent.py)
- [`agents/domain_agents/summarizer_agent.py`](../../agents/domain_agents/summarizer_agent.py)
- [`demos/multi_agent_win/demo.py`](../../demos/multi_agent_win/demo.py)

## Key message

The important win is not "more agents." The win is **clear boundaries**:

- one class decides who should do the work,
- one class gathers evidence,
- one class shapes the explanation.

That is easier to test, explain, and evolve than a single mega-agent with too many jobs.

