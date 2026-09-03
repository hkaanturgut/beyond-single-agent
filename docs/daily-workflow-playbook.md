# Daily workflow playbook

The routine version of the demo: how to use Copilot without overbuilding.

## Start of day

- Open the repo and run `git status --short`
- Check `gh auth status`
- Skim `README.md`, `.github/workflows/ci.yml`, and `.github/workflows/deploy-foundry.yml`
- Ask Copilot for a 5-bullet summary of what changed since yesterday

## While building

- Give Copilot one job at a time
- Prefer file paths, commands, and exact next steps over big explanations
- Use sub-agents when the repo has independent reads or checks
- Keep the scope at the smallest file set that solves the task

## Before a pull request

- Run the repo checks that already exist
- Review the diff once, then ask Copilot for the risk summary
- Commit with a message that names the user-visible change
- Open the PR and let CI tell you whether the change is real

## Before a release or demo

- Read the workflow file, not just the dashboard
- Verify the branch -> PR -> checks -> deploy path still matches the story you plan to tell
- Have one fallback prompt and one local-file fallback ready

## Prompt template

```text
Read [files]. Return [artifact]. Keep it to [length]. Do not add anything outside [scope].
```

Example:

```text
Read README.md, .github/workflows/ci.yml, and .github/workflows/deploy-foundry.yml. Return the branch -> PR -> checks -> deploy story in 5 bullets. Keep it grounded in those files only.
```

## Token hygiene rules

- Prefer short, specific prompts
- Say what not to touch
- Keep one prompt per outcome
- If the answer gets broad, shrink the ask before you ask again
