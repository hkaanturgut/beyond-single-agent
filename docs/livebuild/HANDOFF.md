# Handoff brief — build the presentation deck

You are building a conference deck for a 25-minute main-stage talk **tomorrow**. This
document is self-contained; you do not need the conversation that produced it.

---

## 1. The session

**Title** — *From Prompt to Pipeline: Building a Multi-Agent System in Azure AI Foundry
with GitHub Copilot*
**Venue** — Cloud Summit Toronto 2026, 29 Aug, main stage, 25 minutes, **no Q&A**, recorded.
**Speaker** — Kaan Turgut.

**The published abstract**, which the audience chose this session from:

> Multi-agent systems sound impressive and look intimidating to build. In this session I'll
> build one live, from an empty project to a working pipeline, using GitHub Copilot Agent
> Mode to write the code as I drive.
>
> You'll watch an orchestrator agent and a specialist agent come together in Azure AI
> Foundry, wired to a real tool, with Copilot generating the scaffolding, the agent
> definitions, and the glue code in real time. Along the way I'll show where Copilot Agent
> Mode genuinely accelerates agent development, where it gets things wrong, and the
> decisions you still have to make yourself.
>
> This is a hands-on, watch-me-build-it session, not slides about architecture. You'll leave
> knowing how Foundry's agent model actually fits together, how to use Copilot Agent Mode as
> a real build accelerant instead of fancy autocomplete, and what it takes to get a
> multi-agent pipeline running without the framework getting in your way.

### The constraint you must respect

That abstract promises **"not slides about architecture."** The deck is **scaffolding around
a demo, not a replacement for it.** Keep it thin — eight slides is right, twelve is wrong.
Anything that reads as an architecture lecture is off-brief.

The speaker wants the terminal demo **embedded in the deck** so he never alt-tabs out of it.
That is what you are building. Note the tension and handle it well: he should still do the
**Copilot interaction live**, because that is the part the audience came for. The
recordings replace the slow, network-dependent parts only.

---

## 2. What was built, and what it does

A **spine** — the smallest system that is honestly multi-agent — living at
`docs/livebuild/reference/` in this repository.

```
    ┌─ spine-researcher (web_search)      ─┐
    │                                       ├─→ spine-finalizer ─→ brief.md
    └─ spine-budget    (code_interpreter) ─┘
              ↑ concurrent          ↑ conditional edge if over budget
```

**284 lines, three files:**

| File | Lines | What it is |
|---|---|---|
| `deploy_agents.py` | 111 | creates three PromptAgents in Azure AI Foundry Agent Service, each with only the tools it needs |
| `src/tripspine/workflow.py` | 120 | calls each by name via `agent_reference`, fans out concurrently, one conditional edge |
| `src/tripspine/__main__.py` | 52 | parses the prompt, runs, writes the brief |

**The three ideas that carry the talk:**

1. **The agents are real Foundry resources**, not objects in a process. After
   `deploy_agents.py` runs they are visible in the Foundry portal under *Agents → My
   agents*. You can change one's instructions in the portal and the pipeline picks it up
   with no redeploy. **This is the peak of the session.**
2. **Different tools per agent is what makes them specialists.** `spine-finalizer`
   deliberately has *no* tools — the contrast is the argument. An agent without a distinct
   capability is a prompt variant.
3. **The routing is code, the work is agents.** The fan-out is `asyncio.gather`. The
   over-budget check is four lines of Python. Neither is a model call, on purpose.

---

## 3. You do not need Azure — the recordings are already captured

**Real terminal output with true per-line timings** is in `docs/livebuild/recordings/`.
Captured from live runs against a real Foundry project. The Foundry endpoint has been
scrubbed and replaced with `<your-account>` / `<your-project>`.

| File | What it shows | Duration |
|---|---|---|
| `01-deploy.tsv` | three agents created in Foundry | **2.1s** |
| `02-valletta.tsv` | fan-out, fan-in, within budget, finalize | **39.7s** |
| `03-tokyo-overbudget.tsv` | the conditional edge firing, revision, finalize | **58.6s** |
| `brief-valletta.md` | the actual markdown output | — |
| `brief-tokyo.md` | the actual markdown output, after revision | — |

**Format:** tab-separated, `<seconds-since-start>\t<line of output>`. Example:

```
0.04	3-day trip to Valletta, April, $2200
0.55	  fan-out → spine-researcher, spine-budget  (concurrent)
22.59	  fan-in  ← research 1138 chars, budget 1586 chars
22.59	  conditional → within budget, straight to finalizer
22.59	  → spine-finalizer
39.74	--- written to output/trip-valletta.md ---
```

### How to use them

**Replay them as an animated terminal inside the deck** — plain HTML/CSS/JS, no video
files, no external assets. Read the TSV, emit each line at its timestamp. Two rules:

- **Compress the dead time.** 22 seconds of nothing while two agents think is correct
  behaviour and terrible theatre. Scale the gaps — cap any single gap at ~1.5s — but put
  the **real** elapsed time on screen as a counter, so nothing is misrepresented. Label it
  `39.7s actual`.
- **Add a replay control.** He will want to re-run a beat while talking. Spacebar or a
  click to restart that terminal.

Colour the output to match the agent palette (below): `spine-researcher` teal,
`spine-budget` amber, `spine-finalizer` stone, the `over budget` line in the alert colour.

**If you want to re-record instead of replaying**, you need an Azure subscription, a Foundry
project, and a `gpt-5-mini` deployment with at least 150 TPM capacity. `infra/main.bicep` in
this repo provisions it. Then `python3 deploy_agents.py` and `PYTHONPATH=src python3 -m
tripspine "..."`. **This is not recommended one day out** — the captured output is real and
sufficient.

---

## 4. The deck to build

There is an existing eight-slide deck at
<https://claude.ai/code/artifact/24071adf-f799-4d5d-b787-e5e30f774cad>. Treat it as a
starting point, not a constraint — but **the structure below is load-bearing** and was
timed against the 25-minute slot.

| # | Slide | Time | Contains |
|---|---|---|---|
| 1 | Title | 0:00 | Talk title, name, repo. Do not read it aloud. |
| 2 | The shape | 0:00–2:00 | **The only architecture slide.** The three-agent diagram. Thirty seconds. |
| 3 | Two principles | 2:00–4:00 | The two constitution rules Copilot is about to break |
| 4 | Build board | 4:00–19:00 | The five build steps with clock times. **His anchor** — he tabs back here mid-build |
| 5 | **Deploy — embedded terminal** | 8:00 | `01-deploy.tsv` replay + a Foundry portal screenshot beside it |
| 6 | **Run — embedded terminal** | 19:00 | `02-valletta.tsv`, then `03-tokyo-overbudget.tsv` |
| 7 | Where Copilot was wrong | 22:00 | The three failures |
| 8 | The dead branch | 23:00 | The best story in the talk |
| 9 | Close | 24:00 | Four stats, the takeaway line, repo URL |

Slides 5 and 6 are new — that is the work.

### Slide 3 — the two principles, verbatim

> **I. An agent without a distinct capability is a prompt variant, not a specialist.**
> **II. Arithmetic belongs in code, never in a language model.**

Setup line: *"In fifteen minutes Copilot violates both of these, and I catch it because
they're written down."*

### Slide 7 — the three Copilot failures, verbatim

All three produce **code that runs**. That is the whole point.

1. It gave **every agent every tool**, including the finalizer, "just in case."
2. It reached for **chat completions** instead of the Agents service. That builds three
   prompts, not three agents.
3. It wanted a **model call to compare two numbers** — to check whether the budget was over.

Closing line for the slide: *"Every one of those runs. Every one destroys the property the
system exists to have."*

### Slide 8 — the dead branch. Do not compress this one.

> I told the budget agent to come in under budget. So it always did. Which meant the
> conditional edge — the branch that makes this a workflow rather than a pipeline — **never
> fired once.** Nothing looked wrong. The happy path is the one you test.

Then the line the talk ends on:

> **An agent told to produce an acceptable answer will produce one. That is not the same as
> the answer being true.**

### Slide 9 — the numbers, all measured

`3` hosted agents · `284` lines · `10s` to deploy · `42s` to run

Takeaway: *"Copilot wrote most of it. It does not know which properties you are protecting
— those were in the constitution, and they're why I could correct it in real time instead
of finding out in production."*

Repo: `github.com/hkaanturgut/beyond-single-agent`

---

## 5. Design direction

The existing deck uses **Mediterranean night** — the demo plans a trip to Valletta, so the
palette comes from there rather than from generic Azure blue. Keep it or replace it, but
keep the one rule that carries meaning:

```
--ground     #0C1719    deep sea ink
--panel      #132325
--rule       #24393B
--paper      #E8EDEA    limestone
--muted      #7E9396

--researcher #4FC3B0    web_search        — sea teal
--budget     #E5A24B    code_interpreter  — limestone sun
--finalizer  #8FA0A3    NO TOOLS          — stone, deliberately desaturated
--alert      #E0705C
```

**The finalizer being visually quiet is not an aesthetic choice — it encodes that it has no
tool.** Its border is dashed for the same reason. Preserve that; it is the palette carrying
the argument.

Type: Bricolage Grotesque (display/body) + JetBrains Mono (all terminal, labels, data).
Both on Google Fonts.

**Single-theme dark, deliberately** — it is projected in a dark room and a light-mode
surprise mid-talk would be bad.

### Required deck mechanics

- **Fixed 1280×720 stage scaled to viewport**, so type stays proportional on any projector
- `←` `→` / space to navigate, `O` overview grid, `N` speaker notes, `F` fullscreen
- A **beat rail** along the bottom showing which of the ~6 phases he is in
- **Speaker notes per slide** (`data-notes`) — he presents from these
- Self-contained: no external assets except Google Fonts. Inline everything else.

---

## 6. Things that will bite you

- **The conditional beat needs Tokyo at `$120`, not `$400`.** At $400 the budget agent
  sometimes prices the trip *under* target and the branch does not fire — pricing is a
  judgement call, so it is not deterministic. $120 is below any honest three-day total.
  Verified firing on three consecutive runs. `03-tokyo-overbudget.tsv` is the $120 run.
- **The over-budget path is 58s, the happy path 40s.** The revision is a fourth call. If
  both terminals autoplay back to back that is 100 seconds of stage time — compress the
  gaps aggressively.
- **Do not put the real Foundry endpoint on a slide.** It is scrubbed in the recordings;
  keep it that way.
- **Eight or nine slides. Not more.** The abstract promised the opposite of a slide deck.

---

## 7. What the speaker still does live

Say this back to him so expectations are aligned:

- **`/speckit.specify` in Copilot** — the one Spec Kit command run on stage
- **`/speckit.implement`** producing `deploy_agents.py` and `workflow.py`, with him
  catching the three failures in real time
- **Refreshing the Foundry portal** after the deploy recording plays — the agents really are
  there, and that moment should be live even though the deploy itself is recorded

The recordings cover the waiting: the deploy, and the two runs.

---

## 8. Source of truth

Everything is on `main` at `github.com/hkaanturgut/beyond-single-agent`:

| Path | What |
|---|---|
| `docs/livebuild/README.md` | the full stage script — every prompt, timed, with the corrections and recovery lines |
| `docs/livebuild/reference/` | the working 284-line implementation |
| `docs/livebuild/recordings/` | the captured terminal output you are embedding |
| `.specify/memory/constitution.md` | the principles |
| `src/trip_planner/` | the full five-agent production version — the close points here |
