# Live build — empty directory to a working multi-agent pipeline, 25 minutes

## What gets built

Not this repository. A **spine** of it — the same architecture at a size that genuinely
fits the slot:

```
    ┌─ spine-researcher (web_search)      ─┐
    │                                       ├─→ spine-finalizer ─→ brief.md
    └─ spine-budget    (code_interpreter) ─┘
              ↑ concurrent          ↑ conditional edge if over budget
```

**284 lines. Three hosted agents. Deploys in 10 seconds, runs in 42.**

Measured on a cold start — the three agents deleted from Foundry first, then rebuilt
exactly as you will on stage. The over-budget path takes **68 seconds**, because the
revision is a fourth call. Budget the extra 26 seconds before you promise that beat.

Reference implementation: [`reference/`](reference/). It is verified working against
`trip-planner-prod` — the three agents are deployed right now. You are re-deriving it in
front of people, which is what lets you correct Copilot the moment it drifts.

The full five-agent version with the optimizer is this repository, and it is the close.

---

## The honest timing problem, and how it is solved

A complete Spec Kit cycle — `constitution` → `specify` → `clarify` → `plan` → `tasks` →
`implement` — is **20 to 45 minutes before a single line runs.** Each command generates a
long document. That is the whole session with nothing on screen but Copilot thinking.

So: **one Spec Kit command live, the rest pre-generated and shown.** Say so plainly —

> "I ran `/speckit.plan` and `/speckit.tasks` this morning. Here's what they gave me.
> Watch what happens when I hand the tasks to Copilot."

Nobody minds. Everybody minds four minutes of a spinner.

Pre-generate onto a branch before the talk:

```bash
git checkout -b livebuild-prepared
# run /speckit.plan and /speckit.tasks in Copilot, commit the artifacts
git checkout -b live      # the branch you present from
```

---

## Pre-flight, 30 minutes before

```bash
az login                                     # most likely failure, by a distance
az account show                              # right subscription
cd ~/repos/hkaanturgut/beyond-single-agent/docs/livebuild/reference
source ../../../.venv/bin/activate
python3 deploy_agents.py                     # 10s — proves Foundry is reachable
PYTHONPATH=src python3 -m tripspine          # 42s — proves the whole chain
```

**Delete the three `spine-*` agents before you start.** The portal going from five agents
to eight *while the room watches* is the beat; them already being there is not.

Then open, and leave open:
- the Foundry portal on **Agents → My agents**
- an empty directory, terminal, and VS Code with Copilot Agent Mode

---

## 0:00–2:00 · Where we are going

Run the finished spine once. Let the brief render. Then:

> "Three agents. Two of them ran at the same time. One of them wrote code to do the
> arithmetic because language models cannot count. In twenty minutes we will have built
> that from an empty folder, and I will not type most of it."

Then `cd` into an empty directory and stay there.

---

## 2:00–4:00 · The constitution

Show `.specify/memory/constitution.md` — you already have one. Do not generate it live;
read the two principles that will actually bite:

> **An agent without a distinct capability is a prompt variant, not a specialist.**
> **Arithmetic belongs in code, not in a language model.**

> "These aren't decoration. In fifteen minutes Copilot is going to violate both, and I'm
> going to catch it because they're written down."

---

## 4:00–8:00 · `/speckit.specify` — live

```
/speckit.specify A trip planning pipeline. Three specialist agents hosted in Azure AI
Foundry Agent Service: a researcher with the hosted web_search tool, a budget analyst with
the hosted code_interpreter tool, and a finalizer with no tools at all. The researcher and
the budget analyst run concurrently. Their outputs are aggregated, and if the budget comes
back over target the budget analyst is asked once for a revision before the finalizer
writes a markdown brief.
```

While it generates, talk about what you just asked for — specifically that you named the
tools, because the tools are what make them specialists.

When it lands, read **one** functional requirement aloud. Not all of them.

Then handoff to plan, and cut:

> "I ran plan and tasks this morning — they take about six minutes and I'd rather spend
> those on code."

`git checkout livebuild-prepared -- specs/` and show `tasks.md`.

---

## 8:00–14:00 · The agents, and the portal moment

**This is the peak of the session. Protect the time for it.**

**Prompt 1**

> From `specs/00N-.../tasks.md`, implement `deploy_agents.py`. Deploy three PromptAgents to
> Azure AI Foundry Agent Service using `azure-ai-projects`: `spine-researcher` with
> `WebSearchTool`, `spine-budget` with `CodeInterpreterTool`, and `spine-finalizer` with no
> tools. Keep the specs in a table at module level. Use `client.agents.create_version` so
> re-running is idempotent, and `AzureCliCredential`.

**What Copilot gets wrong, and what to say:**

- **It gives every agent every tool**, or gives the finalizer a tool "just in case."
  *"Constitution, first principle. If they all have the same tools they're the same agent
  with different adjectives."*
- **It reaches for `AzureOpenAI` or the chat-completions API** instead of the Agents
  service. *"That builds three prompts. I want three agents — things that exist in Foundry
  after this script finishes."*
- **It invents a `create_agent` call.** The method is `create_version`, and the reason
  matters: *"agents are versioned resources. I can change one in the portal without
  touching this code."*

Then run it — **10 seconds** — and **refresh the Foundry portal.**

> "Those are not in my code any more. They're in Foundry. Different tools each. I can open
> one, change its instructions, and my pipeline picks it up without a redeploy."

Let that sit. It is the single most convincing thing in the talk.

---

## 14:00–19:00 · The orchestration

**Prompt 2**

> Implement `src/tripspine/workflow.py`. Call each deployed agent through the Responses API
> using `extra_body={"agent_reference": {"name": ..., "type": "agent_reference"}}`. Run
> `spine-researcher` and `spine-budget` concurrently with `asyncio.gather`, aggregate their
> output, and if the budget exceeds the target ask `spine-budget` once for a revision before
> calling `spine-finalizer`. The over-budget check must be arithmetic in Python, not a model
> call.

**Where to slow down — two moments:**

1. **`agent_reference` is the whole trick.** *"The model name here is almost incidental.
   What decides which instructions and which tools run is that name, resolved against what
   I just deployed."*

2. **Copilot will `await` the two calls in sequence**, or write the over-budget check as a
   fourth model call. Catch the second one:
   > *"Asking a language model whether one number is bigger than another is the kind of
   > thing that demos beautifully and pages you at 3am. Constitution, second principle."*

The Responses client is synchronous, so `asyncio.to_thread` is what makes the concurrency
real rather than a comment. Worth ten seconds.

---

## 19:00–22:00 · Run it

```bash
PYTHONPATH=src python3 -m tripspine "Plan my 3-day trip to Valletta in April with budget \$2200"
```

```
  fan-out → spine-researcher, spine-budget  (concurrent)
  fan-in  ← research 1034 chars, budget 556 chars
  conditional → within budget, straight to finalizer
  → spine-finalizer
```

Then the brief: live April weather with a source URL, a budget table that sums, a gap note.

> "The weather came off the live web ten seconds ago. The budget was computed in Python by
> an agent that wrote the Python itself. And nothing routed anything — I wrote the graph."

**Then Tokyo at `$120`** to fire the conditional edge:

```
  conditional → over budget, asking spine-budget to revise
```

Both branches are verified.

**Use $120, not $400.** At $400 the agent sometimes prices Tokyo *under* target and the
branch does not fire — it is a judgement call, so it is not deterministic. $120 is below
any honest three-day total, so it fires every time. Verified over three consecutive runs.

If time is short, skip this and say you'd have shown it.

---

## 22:00–25:00 · What Copilot did, and what it did not

**Fast at:** the deploy table, the SDK boilerplate, `asyncio.gather`, argument parsing,
the markdown writer. Mechanical, well-attested shapes.

**Wrong about the things that mattered:** it wanted to hand every agent every tool, it
wanted chat-completions instead of the Agents service, and it wanted a model call to
compare two numbers. **All three produce working code.** All three destroy the property
the system exists to have.

**Two bugs I hit building this, both worth thirty seconds:**

> **One.** Every agent asked me a clarifying question instead of answering. `"Do you want
> the budget to include flights?"` — addressed to nobody, because there is no human inside
> a workflow. One line of instructions fixes it. That is not a prompt-engineering trick, it
> is a consequence of where the agent runs, and you only find it by running it.
>
> **Two, and this is the better story.** I told the budget agent to come in at or under the
> stated budget. It always did. So the conditional edge — the branch that makes this a
> workflow rather than a pipeline — **never fired once**, and the demo looked perfect,
> because the happy path is the one you test. The fix was to stop instructing the agent
> toward the answer: price it honestly, and let *code* decide whether that is over budget.
>
> An agent told to produce an acceptable answer will produce one. That is not the same as
> the answer being true.

**Close:**

> Copilot wrote most of that. It does not know which properties I am protecting — those
> were in the constitution, and they're why I could correct it in real time instead of
> discovering it in production.

Then: *"this is the spine. The full version has five agents, an optimizer on the
conditional branch, and Bicep for the infrastructure"* →
`github.com/hkaanturgut/beyond-single-agent`

---

## The deck

Eight slides, scaffolding only: <https://claude.ai/code/artifact/24071adf-f799-4d5d-b787-e5e30f774cad>

`←→` navigate · `O` overview · `N` speaker notes · `F` fullscreen. Slide 4 is the build
board — tab back to it whenever the room needs re-orienting mid-build.

---

## Recovery lines

- **Foundry 401.** *"The failure I'd have bet on. Twenty seconds."* → `az login`
- **Copilot output unusable.** *"Wrong shape — here's the one I'd ship."* → paste from
  `reference/`, keep moving.
- **An agent hangs.** Ctrl-C. *"Hosted tools run in Foundry's loop, and web search
  sometimes takes its time."* → re-run; it is 38 seconds.
- **Deploy fails.** The agents from pre-flight are still there. Skip to the workflow and
  narrate the deploy script instead.
- **Running long at 19:00.** Cut the conditional-edge re-run, not the portal moment.
