"""Run the spine.

    python -m tripspine "Plan my 3-day trip to Valletta in April with budget $2200"
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from tripspine.workflow import TripRequest, foundry_from_env, run

load_dotenv()

DEFAULT = "Plan my 3-day trip to Valletta in April with budget $2200"

OUTPUT = Path("output")


def parse(text: str) -> TripRequest:
    """Pull the four fields out of one sentence.

    A regex, not a model call. Parsing your own demo prompt with an LLM adds a second of
    latency, a source of nondeterminism, and nothing else.
    """
    destination = m.group(1).strip() if (m := re.search(r"to ([A-Z][\w\s]+?) in ", text)) else "Valletta"
    month = m.group(1) if (m := re.search(r" in (\w+)", text)) else "April"
    budget = int(m.group(1).replace(",", "")) if (m := re.search(r"\$([\d,]+)", text)) else 2200
    days = int(m.group(1)) if (m := re.search(r"(\d+)-day", text)) else 3
    return TripRequest(destination=destination, month=month, budget_usd=budget, days=days)


async def main() -> None:
    prompt = " ".join(sys.argv[1:]) or DEFAULT
    request = parse(prompt)
    print(f"\n{request.days}-day trip to {request.destination}, {request.month}, ${request.budget_usd}\n")

    brief = await run(request, foundry_from_env())

    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / f"trip-{request.destination.lower().replace(' ', '-')}.md"
    path.write_text(brief)
    print(f"\n--- written to {path} ---\n")
    print(brief)


if __name__ == "__main__":
    asyncio.run(main())
