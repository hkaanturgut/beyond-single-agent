"""The orchestration: fan-out, fan-in, one conditional edge.

    ┌─ spine-researcher (web_search) ─┐
    │                                  ├─→ aggregate ─→ spine-finalizer ─→ brief.md
    └─ spine-budget    (code_interp) ─┘

The two specialists are independent, so they run concurrently — `asyncio.gather`, not a
loop. That is not an optimisation; sequentially this demo takes twice as long on stage and
the audience watches a spinner.

The conditional edge is the second half of the pattern: if the budget agent comes back over
target, the work goes back for a revision before finalising. One branch, but it is the
branch that makes this a workflow rather than a pipeline.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

MAX_TOKENS = 3000


@dataclass
class TripRequest:
    destination: str
    month: str
    budget_usd: int
    days: int = 3

    def as_prompt(self) -> str:
        return (
            f"Destination: {self.destination}\nMonth: {self.month}\n"
            f"Budget: ${self.budget_usd} USD\nDuration: {self.days} days"
        )


class Foundry:
    """Calls a *named, deployed* agent through the Responses API.

    `agent_reference` is the whole trick. The model name is almost incidental — what
    decides which instructions and which tools run is the agent name, resolved by Foundry
    against what `deploy_agents.py` created. Change the agent in the portal and this code
    picks it up with no redeploy.
    """

    def __init__(self, endpoint: str, model: str) -> None:
        from azure.ai.projects import AIProjectClient
        from azure.identity import AzureCliCredential

        self._project = AIProjectClient(endpoint=endpoint, credential=AzureCliCredential())
        self._client = self._project.get_openai_client()
        self._model = model

    def _call(self, agent_name: str, message: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=message,
            max_output_tokens=MAX_TOKENS,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for block in getattr(item, "content", []):
                    if text := getattr(block, "text", None):
                        return text
        return getattr(response, "output_text", "") or ""

    async def ask(self, agent_name: str, message: str) -> str:
        """The Responses client is synchronous, so it goes to a thread.

        Without this, `asyncio.gather` below would await two blocking calls in sequence and
        the concurrency would be a comment rather than a fact.
        """
        return await asyncio.to_thread(self._call, agent_name, message)


TOTAL_PATTERN = re.compile(r"TOTAL:\s*\$?\s*([\d,]+)", re.I)


def parse_total(breakdown: str) -> int | None:
    """Read the analyst's declared total.

    The agent is asked to end with `TOTAL: $N` precisely so this is a parse and not a
    guess. An earlier version took the largest number anywhere in the text, which happily
    matched a year, a distance, and a phone number.
    """
    matches = TOTAL_PATTERN.findall(breakdown)
    if not matches:
        return None
    return int(matches[-1].replace(",", ""))


def over_budget(breakdown: str, target: int) -> bool:
    """The condition on the conditional edge.

    Deliberately arithmetic rather than a model call: asking a language model whether one
    number exceeds another is the kind of thing that demos beautifully and pages you later.

    The branch only exists because the analyst is told to price *honestly* rather than to
    force the total under target. Instruct it to stay under and this edge is dead code —
    which is exactly what happened the first time, and it looked fine, because the happy
    path is the one you test.
    """
    total = parse_total(breakdown)
    return total is not None and total > target


async def run(request: TripRequest, foundry: Foundry, log=print) -> str:
    prompt = request.as_prompt()

    log("  fan-out → spine-researcher, spine-budget  (concurrent)")
    research, budget = await asyncio.gather(
        foundry.ask("spine-researcher", prompt),
        foundry.ask("spine-budget", prompt),
    )
    log(f"  fan-in  ← research {len(research)} chars, budget {len(budget)} chars")

    if over_budget(budget, request.budget_usd):
        log("  conditional → over budget, asking spine-budget to revise")
        budget = await foundry.ask(
            "spine-budget",
            f"{prompt}\n\nThis breakdown exceeds the budget. Revise it to come in at or "
            f"under ${request.budget_usd}, and show the new total.\n\n{budget}",
        )
    else:
        log("  conditional → within budget, straight to finalizer")

    log("  → spine-finalizer")
    return await foundry.ask(
        "spine-finalizer",
        f"{prompt}\n\n## Research\n{research}\n\n## Budget\n{budget}",
    )


def foundry_from_env() -> Foundry:
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    return Foundry(endpoint, os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini"))
