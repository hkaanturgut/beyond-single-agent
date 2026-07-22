"""Optional MCP (Model Context Protocol) bridge.

This module is a STUB.  MCP-based enrichment is opt-in and NOT required for
core workflow success (FR-012).  Enable it by setting:

    MCP_ENABLED=true
    MCP_TAVILY_URL=https://...
    MCP_FILESYSTEM_URL=https://...
    MCP_API_KEY=...

When MCP is disabled (the default) all functions in this module return empty
results immediately without making any network calls.
"""

from __future__ import annotations

import os
from typing import Any, Dict

_MCP_ENABLED = os.getenv("MCP_ENABLED", "false").lower() == "true"


async def search_destination(destination: str, month: str) -> Dict[str, Any]:
    """Optional live-search enrichment for destination data.

    Returns an empty dict when MCP is disabled.
    """
    if not _MCP_ENABLED:
        return {}

    # TODO: Implement real MCP call via mcp_tavily_url when MCP is enabled.
    return {}


async def write_output_file(path: str, content: str) -> bool:
    """Optional MCP-based file write (falls back to local write when disabled)."""
    if not _MCP_ENABLED:
        return False

    # TODO: Implement real MCP filesystem write when MCP is enabled.
    return False
