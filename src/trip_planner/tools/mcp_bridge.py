"""MCP (Model Context Protocol) configuration for Foundry-hosted agents.

In this project, tools run **server-side inside Azure AI Foundry**, not in this Python
process.  Each specialist agent is deployed with its tools attached to its
``PromptAgentDefinition`` (see ``scripts/deploy_agents.py``); Foundry executes the tool
loop when the agent is invoked via the Responses API.  That means:

  * Hosted tools (``web_search``, ``code_interpreter``) need no client code here.
  * A remote **MCP server** is attached the same way — as an ``MCPTool`` on the agent —
    rather than being called from this module.

This module therefore just centralises how the optional MCP server is *configured*, so
the deploy script and docs share one source of truth.  MCP is opt-in: when
``MCP_SERVER_URL`` is unset, agents use their hosted tools only and nothing here runs.

Enable a remote MCP server by exporting::

    MCP_SERVER_LABEL=trip_tools
    MCP_SERVER_URL=https://your-mcp-server.example.com/sse
    MCP_ALLOWED_TOOLS=search,lookup      # optional allow-list (comma-separated)
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional


def mcp_enabled() -> bool:
    """True when a remote MCP server URL is configured."""
    return bool(os.getenv("MCP_SERVER_URL", "").strip())


def mcp_config() -> Optional[Dict[str, object]]:
    """Return the MCP server configuration, or ``None`` when MCP is disabled.

    The returned dict mirrors the fields of ``azure.ai.projects.models.MCPTool`` so the
    deploy script (and any future in-process MCP client) can consume it directly.
    """
    server_url = os.getenv("MCP_SERVER_URL", "").strip()
    if not server_url:
        return None

    config: Dict[str, object] = {
        "server_label": os.getenv("MCP_SERVER_LABEL", "trip_tools").strip(),
        "server_url": server_url,
        "require_approval": "never",
    }
    allowed = os.getenv("MCP_ALLOWED_TOOLS", "").strip()
    if allowed:
        config["allowed_tools"] = _split_allow_list(allowed)
    return config


def _split_allow_list(raw: str) -> List[str]:
    return [tool.strip() for tool in raw.split(",") if tool.strip()]
