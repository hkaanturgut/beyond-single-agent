"""Unit tests — deploy_agents tool specs and MCP config (no Azure calls).

These validate the *shape* of the deployment config: each agent declares the right
tools, and the optional MCP tool is env-gated.  They do not contact Foundry.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

# Load scripts/deploy_agents.py as a module (it is a script, not a package member).
_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "deploy_agents", _ROOT / "scripts" / "deploy_agents.py"
)
deploy_agents = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(deploy_agents)  # type: ignore[union-attr]

pytest.importorskip("azure.ai.projects", reason="azure-ai-projects not installed in this venv")


def _spec_for(name: str) -> dict:
    return next(s for s in deploy_agents.AGENT_SPECS if s["name"] == name)


class TestAgentSpecs:
    def test_all_five_agents_present(self):
        names = {s["name"] for s in deploy_agents.AGENT_SPECS}
        assert names == {
            "researcher-agent",
            "planner-agent",
            "budget-agent",
            "optimizer-agent",
            "finalizer-agent",
        }

    def test_researcher_has_web_search(self):
        assert deploy_agents.WEB_SEARCH in _spec_for("researcher-agent")["tools"]

    def test_planner_budget_optimizer_have_code_interpreter(self):
        for name in ("planner-agent", "budget-agent", "optimizer-agent"):
            assert deploy_agents.CODE_INTERPRETER in _spec_for(name)["tools"]

    def test_finalizer_has_no_tools(self):
        assert _spec_for("finalizer-agent")["tools"] == []


class TestBuildTools:
    def test_web_search_resolves_to_hosted_tool(self):
        tools = deploy_agents._build_tools([deploy_agents.WEB_SEARCH], "researcher-agent")
        types = [t.get("type") for t in tools]
        assert "web_search" in types

    def test_code_interpreter_resolves(self):
        tools = deploy_agents._build_tools([deploy_agents.CODE_INTERPRETER], "budget-agent")
        assert [t.get("type") for t in tools] == ["code_interpreter"]


class TestMcpGating:
    def test_no_mcp_by_default(self, monkeypatch):
        monkeypatch.delenv("MCP_SERVER_URL", raising=False)
        tools = deploy_agents._build_tools([deploy_agents.WEB_SEARCH], "researcher-agent")
        assert all(t.get("type") != "mcp" for t in tools)

    def test_mcp_attached_to_researcher_when_configured(self, monkeypatch):
        monkeypatch.setenv("MCP_SERVER_URL", "https://mcp.example.com/sse")
        monkeypatch.setenv("MCP_SERVER_LABEL", "trip_tools")
        tools = deploy_agents._build_tools([deploy_agents.WEB_SEARCH], "researcher-agent")
        assert any(t.get("type") == "mcp" for t in tools)

    def test_mcp_not_attached_to_other_agents(self, monkeypatch):
        monkeypatch.setenv("MCP_SERVER_URL", "https://mcp.example.com/sse")
        tools = deploy_agents._build_tools([deploy_agents.CODE_INTERPRETER], "budget-agent")
        assert all(t.get("type") != "mcp" for t in tools)
