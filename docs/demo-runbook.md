# Demo runbook

Conference-ready run-of-show for a 25-30 minute live demo of "A day of an Engineer with GitHub Copilot".

## 15 minutes before

- `git status --short`
- `gh auth status`
- Open `README.md`, `docs/demo-runbook.md`, `.github/workflows/ci.yml`, `.github/workflows/deploy-foundry.yml`
- Open Copilot CLI in the repo root
- Keep one terminal on `gh`/`git`, one on the repo, one on Copilot
- If Azure or GitHub auth is flaky, switch to the fallback lines in `docs/demo-fallbacks.md`

## 0:00-2:00 - Set the frame

Say: this is not a slide tour; it is a working repo, and Copilot is helping me move through it.

Command:

```bash
git branch --show-current
git status --short
```

Then paste this into Copilot CLI:

```text
Read README.md, docs/architecture.md, .github/workflows/ci.yml, .github/workflows/deploy-foundry.yml, src/trip_planner/cli.py, and scripts/deploy_agents.py.

Work like an engineer, not a narrator:
1. Delegate the file-reading and workflow-summary work across sub-agents.
2. Return one concise map of the repo: what runs locally, what runs in GitHub Actions, and what the Foundry deploy path is.
3. Keep the answer to 5 bullets and call out any missing demo risk.
```

## 2:00-7:00 - Agentic workflow in Copilot CLI

Say: I want Copilot to do the reading, but I still own the shape of the work.

Paste this:

```text
Create a minimal demo package for this repo. Keep it doc-only unless a file is missing.

Use sub-agents for three separate checks:
- one reads the pipeline files and extracts the branch -> PR -> checks -> deploy story
- one reads the runtime path and extracts the local run story
- one checks whether the repo already has enough material for a live demo or needs any tiny additions

Then synthesize the result into the smallest set of files I should add or update.
```

Follow-up if the answer is vague:

```text
Be stricter. Re-read the repo and give me only concrete file paths, exact commands, and one sentence on why each file matters.
```

## 7:00-12:00 - MCP-connected GitHub context

Say: now I want repo context from GitHub, not just local file browsing.

Paste this:

```text
Use GitHub MCP context for hkaanturgut/beyond-single-agent.

Inspect the repo files that matter for the story: README.md, .github/workflows/ci.yml, .github/workflows/deploy-foundry.yml, docs/architecture.md, and scripts/deploy_agents.py.

Summarize the exact pipeline path for the audience:
branch -> commit -> PR -> CI -> deploy workflow -> release-ready demo.

Keep it grounded in the repo contents and name the two workflow files explicitly.
```

If MCP auth is slow, switch to local proof:

```bash
sed -n '1,160p' .github/workflows/ci.yml
sed -n '1,220p' .github/workflows/deploy-foundry.yml
```

## 12:00-17:00 - Skills usage in practice

Say: I am going to use a skill, not hand-roll a plan in chat.

Paste this:

```text
/speckit.specify Create a conference demo package for this repo.

Keep the scope tight:
- add a README entry that links the demo assets
- add a runbook with exact paste-ready prompts
- add a short speaker script
- add offline/no-auth fallbacks
- add a daily-workflow checklist

Do not change runtime code unless a file is truly missing.
```

Then:

```text
/speckit.tasks Turn that spec into a short, dependency-ordered file list.
```

And:

```text
/speckit.implement Implement only the smallest set of files needed for the demo package.
```

If the tool starts inventing extra work, stop it:

```text
No extra abstractions. No new code paths. Keep it to docs unless the pipeline story is broken.
```

## 17:00-22:00 - Pipeline story, live

Say: the point is not just that the code exists; the point is that the repo can ship it.

Commands:

```bash
git checkout -b copilot-demo-package
git add README.md docs/demo-runbook.md docs/demo-script.md docs/demo-fallbacks.md docs/daily-workflow-playbook.md
git commit -m "docs: add conference demo package"
git push -u origin copilot-demo-package
gh pr create --fill
gh pr checks --watch
```

If you want to show release wiring on the same repo:

```bash
gh workflow run "Deploy Azure infrastructure and agents" \
  --field resource_group_name=rg-beyond-single-agent \
  --field location=eastus \
  --field environment_name=demo \
  --field model_deployment_name=gpt-5-mini \
  --field deploy_agents=true
```

If the live deploy cannot run, show the workflow file and narrate the release path from it.

## 22:00-26:00 - Token hygiene

Say: shorter prompts save time and reduce bad output.

Bad prompt:

```text
Can you clean up the repo and make the demo better?
```

Good prompt:

```text
Update README.md with a demo entry that links docs/demo-runbook.md, docs/demo-script.md, docs/demo-fallbacks.md, and docs/daily-workflow-playbook.md. Keep the change doc-only and do not touch runtime code.
```

Caveman version:

```text
Read README.md + .github/workflows/*.yml. Give me the shortest branch -> PR -> checks -> deploy story in 5 bullets.
```

## 26:00-28:00 - Close

Say: the repo already has the pipeline; Copilot helps me move through it with less thrash.

Final command:

```bash
git status --short
```
