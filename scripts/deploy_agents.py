"""Deploy trip-planner agents to Azure AI Foundry Agent Service — *with tools*.

Creates (or updates) five specialist PromptAgents visible in the Foundry UI, each
attached to the capabilities it actually needs.  Agents without distinct tools are
just prompt variants;  attaching heterogeneous, hosted tools is what makes them
genuinely specialised:

  - researcher-agent  — WebSearchTool (+ optional MCP)  live destination research
  - planner-agent     — CodeInterpreterTool             deterministic scheduling
  - budget-agent      — CodeInterpreterTool             exact cost arithmetic
  - optimizer-agent   — CodeInterpreterTool             recompute revised budget
  - finalizer-agent   — (no tool)                       pure synthesis

All tools are *Foundry-hosted*: they run inside the Foundry tool loop when the agent
is invoked via the Responses API (``agent_reference``), so the Python workflow needs
zero tool-plumbing changes.  The WorkflowBuilder + ConcurrentBuilder still orchestrate
concurrent fan-out and conditional routing;  each hosted agent contributes one node.

Web search and code interpreter are OpenAI-native hosted tools — they do NOT require a
billable "Grounding with Bing Search" resource, so they work on a pay-as-you-go
subscription.

Optional remote MCP tool (attached to the researcher) is enabled by setting::

    MCP_SERVER_LABEL=trip_tools
    MCP_SERVER_URL=https://your-mcp-server.example.com/sse
    MCP_ALLOWED_TOOLS=search,lookup      # optional, comma-separated allow-list

When those are unset the researcher uses hosted web search only (robust demo default).

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
# Model + tool identifiers
# ---------------------------------------------------------------------------

_MODEL = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")

# Symbolic tool ids resolved to real SDK Tool objects in ``_build_tools`` (keeps the
# AGENT_SPECS table readable and import-free at module load time).
WEB_SEARCH = "web_search"
CODE_INTERPRETER = "code_interpreter"

# ---------------------------------------------------------------------------
# Agent definitions — name, description, tools, model instructions
# ---------------------------------------------------------------------------

AGENT_SPECS: list[dict] = [
    {
        "name": "researcher-agent",
        "description": "Gathers destination intelligence: attractions, weather, events, cultural tips.",
        "tools": [WEB_SEARCH],  # + optional MCP (see _build_tools)
        # Low reasoning effort keeps latency down and leaves output budget for the final
        # message — gpt-5-mini otherwise spends the whole cap on reasoning during tool use.
        "reasoning_effort": "low",
        "instructions": (
            "You are a travel research specialist. "
            "Use the web_search tool to ground your answer in CURRENT information for the "
            "specific destination and travel month (real attractions, seasonal weather, and "
            "events happening that month). Do not rely on memory alone. "
            "Given a destination and travel month, provide a concise JSON object with keys: "
            "attractions (list of 4-6 top sights), weather_summary (1-2 sentences), "
            "events (list of notable events that month), cultural_tips (list of 3-4 tips). "
            "After any tool use, your FINAL message must be ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "planner-agent",
        "description": "Drafts a 3-day itinerary with realistic, conflict-checked time slots.",
        "tools": [CODE_INTERPRETER],
        "reasoning_effort": "low",
        "instructions": (
            "You are a trip-planning specialist. "
            "Use the code_interpreter tool to sequence activities and DETECT scheduling "
            "conflicts programmatically: build the day's time slots, then verify no two "
            "slots on the same day overlap before finalising. "
            "Given a destination, travel month, budget, and research notes, "
            "draft a 3-day itinerary as a JSON object with keys: "
            "days (array of 3 day objects, each with day_number (1-3) and slots "
            "(array of {start_time, end_time, activity, location_hint})), "
            "conflict_flags (array of strings describing any scheduling conflicts found). "
            "After any tool use, your FINAL message must be ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "budget-agent",
        "description": "Estimates trip costs with exact, tool-computed arithmetic.",
        "tools": [CODE_INTERPRETER],
        "reasoning_effort": "low",
        "instructions": (
            "You are a travel budget specialist. "
            "Use the code_interpreter tool to compute the arithmetic exactly — sum the line "
            "items with real calculation, never mental math, and confirm the total. "
            "Given a destination, travel month, and budget limit, "
            "estimate costs as a JSON object with keys: "
            "flight_estimate (number), hotel_estimate (number, 3 nights), "
            "food_estimate (number, 3 days), activity_estimate (number), "
            "total_estimate (the tool-computed sum of the above), "
            "confidence (low|medium|high based on data availability). "
            "All values are in USD. "
            "After any tool use, your FINAL message must be ONLY valid JSON, no markdown fences."
        ),
    },
    {
        "name": "optimizer-agent",
        "description": "Revises an over-budget or conflict-containing proposal and recomputes the budget.",
        "tools": [CODE_INTERPRETER],
        "reasoning_effort": "low",
        "instructions": (
            "You are a trip optimisation specialist. "
            "Given an over-budget or conflict-containing trip proposal, suggest concrete "
            "adjustments, then use the code_interpreter tool to RECOMPUTE the revised budget "
            "so the new total genuinely reflects your changes (do not estimate the new total). "
            "Respond in plain text (not JSON) using this exact format:\n\n"
            "CHANGES_APPLIED:\n- <change 1>\n- <change 2>\n\n"
            "REMAINING_TRADEOFFS:\n- <tradeoff 1>\n- <tradeoff 2>\n\n"
            "REVISED_BUDGET:\n"
            "Flight: $<amount>, Hotel: $<amount>, Food: $<amount>, Activities: $<amount>, "
            "Total: $<amount>"
        ),
    },
    {
        "name": "finalizer-agent",
        "description": "Writes the polished markdown trip brief with packing/prep tips (no tools — pure synthesis).",
        "tools": [],  # deliberate: not every agent needs a tool
        "instructions": (
            "You are a travel writer. "
            "Given trip research, an itinerary, and a budget breakdown, "
            "write a packing/preparation section of 4-6 bullet points appropriate "
            "for the destination and month. Return plain text bullets only."
        ),
    },
]


def _build_tools(tool_ids: list[str], agent_name: str) -> list:
    """Resolve symbolic tool ids to SDK Tool objects, plus optional MCP for the researcher."""
    from azure.ai.projects.models import CodeInterpreterTool, WebSearchTool

    tools: list = []
    for tid in tool_ids:
        if tid == WEB_SEARCH:
            tools.append(WebSearchTool())
        elif tid == CODE_INTERPRETER:
            tools.append(CodeInterpreterTool())

    # Optional remote MCP tool — attached to the researcher when configured.
    if agent_name == "researcher-agent":
        mcp_tool = _maybe_mcp_tool()
        if mcp_tool is not None:
            tools.append(mcp_tool)

    return tools


def _maybe_mcp_tool():
    """Build an MCPTool from env config, or return None when MCP is not configured."""
    server_url = os.getenv("MCP_SERVER_URL", "").strip()
    server_label = os.getenv("MCP_SERVER_LABEL", "trip_tools").strip()
    if not server_url:
        return None

    from azure.ai.projects.models import MCPTool

    kwargs: dict = {
        "server_label": server_label,
        "server_url": server_url,
        # Hosted execution: never block on interactive approval during the workflow.
        "require_approval": "never",
    }
    allowed = os.getenv("MCP_ALLOWED_TOOLS", "").strip()
    if allowed:
        kwargs["allowed_tools"] = [t.strip() for t in allowed.split(",") if t.strip()]

    try:
        return MCPTool(**kwargs)
    except TypeError:
        # Older/newer SDKs may name the approval field differently; retry without it.
        kwargs.pop("require_approval", None)
        return MCPTool(**kwargs)


def deploy_agents(endpoint: str) -> dict[str, str]:
    """Create or update all trip-planner agents with their tools. Returns {name: version}."""
    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import PromptAgentDefinition
        from azure.identity import AzureCliCredential, DefaultAzureCredential
    except ImportError as exc:
        print(f"ERROR: Missing dependency — {exc}")
        print("Run: pip install azure-ai-projects azure-identity")
        sys.exit(1)

    print(f"Connecting to Foundry project: {endpoint}")
    # Use AzureCliCredential for local dev; DefaultAzureCredential for CI/CD
    try:
        credential = AzureCliCredential()
        credential.get_token("https://ai.azure.com/.default")  # validate it works
    except Exception:
        credential = DefaultAzureCredential()

    client = AIProjectClient(
        endpoint=endpoint,
        credential=credential,
    )

    deployed: dict[str, str] = {}

    for spec in AGENT_SPECS:
        agent_name = spec["name"]
        tools = _build_tools(spec.get("tools", []), agent_name)
        tool_label = ", ".join(t.get("type", "?") for t in tools) if tools else "none"
        print(f"  → Deploying {agent_name}  [tools: {tool_label}] ...", end=" ", flush=True)
        definition_kwargs: dict = {
            "model": _MODEL,
            "instructions": spec["instructions"],
            "tools": tools,
        }
        effort = spec.get("reasoning_effort")
        if effort:
            from azure.ai.projects.models import Reasoning

            definition_kwargs["reasoning"] = Reasoning(effort=effort)
        try:
            version = client.agents.create_version(
                agent_name=agent_name,
                definition=PromptAgentDefinition(**definition_kwargs),
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

    print("\n=== Trip Planner — Foundry Agent Deployment (with tools) ===\n")
    deployed = deploy_agents(endpoint)

    print(f"\nDeployed {len(deployed)}/{len(AGENT_SPECS)} agents:")
    for name, ver in deployed.items():
        print(f"  {name}  (version {ver})")

    if len(deployed) < len(AGENT_SPECS):
        print("\nWARNING: Some agents failed to deploy — check errors above.")
        sys.exit(1)

    print("\nAll agents deployed successfully.")
    print("View them in the Foundry UI: Agents → My agents (each shows its attached tools).")


if __name__ == "__main__":
    main()
