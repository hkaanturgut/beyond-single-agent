# Multi-agent win demo

This demo uses a small orchestrator plus two domain agents to show the same story more cleanly.

## What it shows

- The orchestrator keeps the plan and audience in scope.
- The research agent handles tool usage and evidence gathering.
- The summarizer agent turns structured findings into a speaker-ready narrative.

## Run it

```bash
python demos/multi_agent_win/demo.py --audience python-toronto
python demos/multi_agent_win/demo.py --audience malta
```

For a live Azure AI Foundry pass:

```bash
python demos/multi_agent_win/demo.py --audience malta --live
```

## Speaker notes

- Use the output to narrate the handoff between agents.
- Open `agents/orchestrator.py` to show that the control logic is readable, not magical.
- Open `workflows/pipeline.yaml` to connect the Python code to Foundry orchestration and deployment.

