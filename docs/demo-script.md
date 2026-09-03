# Demo script

Short speaker notes for the live demo.

## Opening

*This is a working repo, not a slide deck. I am going to let Copilot read, summarize, and help me move through the repo quickly.*

## Agentic workflow

*First I want Copilot to break the repo into pieces, because the fastest way to understand a system is to let it read in parallel.*

Recovery line: *If it gets too chatty, I tighten the prompt and ask for file paths only.*

## MCP / GitHub context

*Now I want the same repo story, but grounded in GitHub context so the pipeline path is the source of truth, not my memory.*

Recovery line: *If GitHub auth is slow, I show the workflow files locally and keep going.*

## Skills

*This is where I switch from ad hoc prompting to a skill-driven flow: specify, turn into tasks, then implement the smallest useful slice.*

Recovery line: *If the skill starts overbuilding, I cut the scope back to docs only.*

## Pipeline

*The branch-to-PR-to-checks story is already wired in this repo. I am not inventing the pipeline; I am showing it.*

Recovery line: *If the live workflow is slow, I show the YAML and narrate the same path.*

## Token hygiene

*Short prompts are not about being cute. They reduce noise and make Copilot easier to correct.*

Recovery line: *If the answer is too broad, I restate the task in one sentence and one constraint.*

## Close

*The point is not that Copilot replaces the work. The point is that it keeps the work moving while I stay in control of the shape.*
