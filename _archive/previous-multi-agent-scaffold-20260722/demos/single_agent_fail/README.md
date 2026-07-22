# Single-agent failure demo

This demo is the setup for the rest of the repo: **one agent is asked to do too much at once**.

## What it shows

- Too many concerns share one context window.
- Retrieval, audience adaptation, and error recovery all fight for attention.
- The system has no clean retry boundary because the same agent owns every responsibility.

## Run it

```bash
python demos/single_agent_fail/demo.py
```

## Speaker notes

- Point out that the agent is not "dumb"; it is simply overloaded.
- Emphasize that tool calls are serialized behind one decision-maker.
- Use this to tee up why orchestration and specialization matter in the next demo.

