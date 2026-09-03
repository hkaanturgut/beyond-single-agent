# Demo fallbacks

Offline and no-auth fallbacks for each segment of the live demo.

| Segment | Failure mode | Fallback |
|---|---|---|
| Agentic workflow | Sub-agents are slow or unavailable | Use one concise Copilot prompt and point at `README.md`, `docs/architecture.md`, and `scripts/deploy_agents.py` manually. |
| MCP / GitHub context | GitHub auth or network fails | Read `.github/workflows/ci.yml` and `.github/workflows/deploy-foundry.yml` locally with `sed`. |
| Skills | `/speckit.*` is unavailable | Show the already committed docs package and explain the intended skill flow in one sentence. |
| Pipeline story | `gh` auth or repo access fails | Narrate the branch -> PR -> checks -> deploy path from the workflow files without executing commands. |
| Token hygiene | Live answer is too long | Replace the prompt with the caveman version in the runbook and keep only the 5-bullet answer. |

## If everything is offline

Use the repo as static proof:

- `README.md` for the demo entry
- `docs/demo-runbook.md` for the live order
- `docs/demo-script.md` for transitions
- `docs/daily-workflow-playbook.md` for the routine version
- `.github/workflows/ci.yml` and `.github/workflows/deploy-foundry.yml` for the pipeline story

## Recovery lines

- *No problem, I have the local files and the YAML is enough to prove the path.*
- *If the network comes back, I will re-run the prompt; if not, the demo still holds.*
- *The point here is the workflow shape, not the perfect live fetch.*
