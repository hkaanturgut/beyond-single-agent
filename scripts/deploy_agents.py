"""Deploy trip-planner agents to Azure AI Foundry Agent Service.

Creates (or updates) five specialist PromptAgents visible in the Foundry UI:
  - researcher-agent   — destination research (concurrent fan-out)
  - planner-agent      — day-by-day itinerary (concurrent fan-out)
  - budget-agent       — cost estimation (concurrent fan-out)
  - optimizer-agent    — revision when over budget / conflicts exist
  - finalizer-agent    — polished markdown trip brief

Each agent is a ``PromptAgentDefinition`` backed by a Foundry-hosted model.
The Python workflow (WorkflowBuilder + ConcurrentBuilder) orchestrates them;
the Foundry UI shows each agent's definition, version history, and session logs.

Usage::

    # Deploy with DefaultAzureCredential (run `az login` first)
    python scripts/deploy_agents.py

    # Explicit endpoint override
    FOUNDRY_PROJECT_ENDPOINT=https://... python scripts/deploy_agents.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv(override=False)

# ---------------------------------------------------------------------------
# Agent definitions — name, description, model instructions
# ---------------------------------------------------------------------------

_MODEL = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")

AGENT_SPECS: list[dict] = [
    {
        "name": "researcher-agent",
        "description": "Gathers destination intelligence: attractions, weather, events, cultural tips.",
        "instructions": (
            "You are a travel research specialist. "
            "Given a destination and travel month, provide a concise JSON object with keys: "
            "attractions (list of 4-6 top sights), weather_summary (1-2 sentences), "
            "events (list of notable events that month), cultural_tips (list of 3-4 tips). "
            "Return ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "planner-agent",
        "description": "Drafts a 3-day itinerary with realistic time slots.",
        "instructions": (
            "You are a trip-planning specialist. "
            "Given a destination, travel month, budget, and research notes, "
            "draft a 3-day itinerary as a JSON object with keys: "
            "days (array of 3 day objects, each with day_number (1-3) and slots "
            "(array of {start_time, end_time, activity, location_hint})), "
            "conflict_flags (array of strings describing any scheduling conflicts). "
            "Keep time slots realistic (no overlaps within a day). "
            "Return ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "budget-agent",
        "description": "Estimates trip costs: flights, hotel, food, and activities.",
        "instructions": (
            "You are a travel budget specialist. "
            "Given a destination, travel month, and budget limit, "
            "estimate costs as a JSON object with keys: "
            "flight_estimate (number), hotel_estimate (number, 3 nights), "
            "food_estimate (number, 3 days), activity_estimate (number), "
            "total_estimate (sum of the above), "
            "confidence (low|medium|high based on data availability). "
            "All values are in USD. Return ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "optimizer-agent",
        "description": "Revises an over-budget or conflict-containing trip proposal.",
        "instructions": (
            "You are a trip optimisation specialist. "
            "Given an over-budget or conflict-containing trip proposal, suggest concrete "
            "adjustments. Respond in plain text (not JSON) using this exact format:\n\n"
            "CHANGES_APPLIED:\n- <change 1>\n- <change 2>\n\n"
            "REMAINING_TRADEOFFS:\n- <tradeoff 1>\n- <tradeoff 2>\n\n"
            "REVISED_BUDGET:\n"
            "Flight: $<amount>, Hotel: $<amount>, Food: $<amount>, Activities: $<amount>, "
            "Total: $<amount>"
        ),
    },
    {
        "name": "finalizer-agent",
        "description": "Writes the polished markdown trip brief with packing/prep tips.",
        "instructions": (
            "You are a travel writer. "
            "Given trip research, an itinerary, and a budget breakdown, "
            "write a packing/preparation section of 4-6 bullet points appropriate "
            "for the destination and month. Return plain text bullets only."
        ),
    },
]


def deploy_agents(endpoint: str) -> dict[str, str]:
    """Create or update all trip-planner agents. Returns {name: version}."""
    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import PromptAgentDefinition
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        print(f"ERROR: Missing dependency — {exc}")
        print("Run: pip install azure-ai-projects azure-identity")
        sys.exit(1)

    print(f"Connecting to Foundry project: {endpoint}")
    client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )

    deployed: dict[str, str] = {}

    for spec in AGENT_SPECS:
        agent_name = spec["name"]
        print(f"  → Deploying {agent_name} ...", end=" ", flush=True)
        try:
            version = client.agents.create_version(
                agent_name=agent_name,
                definition=PromptAgentDefinition(
                    model=_MODEL,
                    instructions=spec["instructions"],
                ),
                description=spec["description"],
            )
            deployed[agent_name] = version.version
            print(f"v{version.version} ✓")
        except Exception as exc:
            print(f"FAILED — {exc}")

    return deployed


def main() -> None:
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    if not endpoint:
        print("ERROR: FOUNDRY_PROJECT_ENDPOINT is not set.")
        print("Export it or add it to .env")
        sys.exit(1)

    print("\n=== Trip Planner — Foundry Agent Deployment ===\n")
    deployed = deploy_agents(endpoint)

    print(f"\nDeployed {len(deployed)}/{len(AGENT_SPECS)} agents:")
    for name, ver in deployed.items():
        print(f"  {name}  (version {ver})")

    if len(deployed) < len(AGENT_SPECS):
        print("\nWARNING: Some agents failed to deploy — check errors above.")
        sys.exit(1)

    print("\nAll agents deployed successfully.")
    print("View them in the Foundry UI: Agents → My agents")


if __name__ == "__main__":
    main()
