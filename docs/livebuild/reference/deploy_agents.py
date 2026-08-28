"""Deploy the three spine agents to Azure AI Foundry Agent Service.

This is the file that makes the demo real. After it runs, the agents exist as resources in
Foundry — visible in the portal under Agents → My agents — each carrying only the tools it
actually needs. That last part is the whole argument: an agent without a distinct capability
is a prompt variant, not a specialist.

Two of these tools are Foundry-hosted, meaning they run inside Foundry's own tool loop when
the agent is invoked. There is no client-side plumbing and no billable search resource.

Idempotent: `create_version` on an existing name creates a new version rather than failing,
so this is safe to run repeatedly on stage.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")

WEB_SEARCH = "web_search"
CODE_INTERPRETER = "code_interpreter"

# Name, tools, instructions. Kept as a table so adding a specialist is one entry — which is
# exactly what makes it a good live-build target.
AGENT_SPECS: list[dict] = [
    {
        "name": "spine-researcher",
        "description": "Grounds the trip in current web data: weather, attractions, events.",
        "tools": [WEB_SEARCH],
        "instructions": (
            "You research destinations. Use web search to find, for the given destination "
            "and month: typical weather, three notable attractions, and any seasonal event. "
            "Be concrete and brief — at most 150 words. Cite a URL for each claim.\n\n"
            "Never ask a clarifying question. There is no human in this loop to answer "
            "one. If something is unspecified, state the assumption you made and continue."
        ),
    },
    {
        "name": "spine-budget",
        "description": "Computes a costed breakdown with exact arithmetic.",
        "tools": [CODE_INTERPRETER],
        "instructions": (
            "You are a travel budget analyst. Use the code interpreter to compute a "
            "breakdown — lodging, food, transport, activities — priced realistically for "
            "the destination. Do the arithmetic in code, never in your head.\n\n"
            "Price it honestly. Do NOT force the total under the stated budget: if the "
            "destination genuinely costs more, say so. Deciding what to do about that is "
            "not your job.\n\n"
            "Never ask a clarifying question. There is no human in this loop to answer one. "
            "Exclude international flights and say so as a stated assumption.\n\n"
            "End your reply with a final line in exactly this form, and nothing after it:\n"
            "TOTAL: $<number>"
        ),
    },
    {
        "name": "spine-finalizer",
        "description": "Synthesises the research and the budget into one brief. No tools.",
        # Deliberately empty. The contrast is the point: this agent has no capability
        # because synthesis does not need one, and saying that out loud is what stops
        # "give every agent every tool" from sounding reasonable.
        "tools": [],
        "instructions": (
            "You write the final trip brief in markdown. Given research notes and a budget "
            "breakdown, produce: a one-line summary, a day-by-day outline, and the budget "
            "table. Keep every figure the budget analyst gave you exactly as stated.\n\n"
            "Never ask a clarifying question and never reply with anything but the brief. "
            "If an input is thin, write the brief anyway and note the gap in one line."
        ),
    },
]


def build_tools(tool_ids: list[str]) -> list:
    """Resolve symbolic ids to SDK tool objects."""
    from azure.ai.projects.models import CodeInterpreterTool, WebSearchTool

    tools: list = []
    for tid in tool_ids:
        if tid == WEB_SEARCH:
            tools.append(WebSearchTool())
        elif tid == CODE_INTERPRETER:
            tools.append(CodeInterpreterTool())
    return tools


def main() -> None:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition
    from azure.identity import AzureCliCredential

    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    if not endpoint:
        print("ERROR: FOUNDRY_PROJECT_ENDPOINT is not set. Copy .env.example to .env.")
        sys.exit(1)

    client = AIProjectClient(endpoint=endpoint, credential=AzureCliCredential())

    print(f"\nDeploying {len(AGENT_SPECS)} agents to {endpoint}\n")
    for spec in AGENT_SPECS:
        tools = build_tools(spec["tools"])
        label = ", ".join(t.get("type", "?") for t in tools) if tools else "none"
        print(f"  → {spec['name']:20} [tools: {label}]", end=" ", flush=True)
        version = client.agents.create_version(
            agent_name=spec["name"],
            definition=PromptAgentDefinition(
                model=MODEL, instructions=spec["instructions"], tools=tools
            ),
            description=spec["description"],
        )
        print(f"v{version.version} ✓")

    print("\nOpen the Foundry portal → Agents → My agents. They are there.\n")


if __name__ == "__main__":
    main()
