from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from tools.mcp_tools import MCPToolRegistry, ToolCallRecord, ToolEvidence


@dataclass
class ResearchFinding:
    topic: str
    insight: str
    evidence: list[str]
    recommended_demo_beat: str


@dataclass
class ResearchPacket:
    request: str
    audience: str
    findings: list[ResearchFinding]
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def bullets(self) -> list[str]:
        bullets = [f"{finding.topic}: {finding.insight}" for finding in self.findings]
        bullets.extend(f"Risk to mention: {risk}" for risk in self.risks)
        return bullets


class ResearchAgent:
    """Specialist agent that gathers evidence and surfaces what matters on stage."""

    def __init__(self, tool_registry: MCPToolRegistry, name: str = "research-agent") -> None:
        self.tool_registry = tool_registry
        self.name = name

    def investigate(
        self,
        request: str,
        topics: Iterable[str],
        audience: str,
    ) -> ResearchPacket:
        findings: list[ResearchFinding] = []
        tool_calls: list[ToolCallRecord] = []
        risks: list[str] = []

        for topic in dict.fromkeys(topics):
            search_result = self.tool_registry.search(topic, limit=2)
            lookup_result = self.tool_registry.lookup(topic)
            tool_calls.extend(
                [
                    ToolCallRecord(
                        tool_name=search_result.tool_name,
                        query=search_result.query,
                        result_count=len(search_result.evidence),
                    ),
                    ToolCallRecord(
                        tool_name=lookup_result.tool_name,
                        query=lookup_result.query,
                        result_count=len(lookup_result.evidence),
                    ),
                ]
            )

            merged_evidence = self._merge_evidence(search_result.evidence, lookup_result.evidence)
            findings.append(
                ResearchFinding(
                    topic=topic,
                    insight=self._build_insight(topic, audience, merged_evidence),
                    evidence=[item.excerpt for item in merged_evidence[:2]],
                    recommended_demo_beat=self._demo_beat(topic, audience),
                )
            )

            if not merged_evidence:
                risks.append(
                    f"{topic} has thin supporting evidence, so the orchestrator should avoid overselling certainty."
                )

        return ResearchPacket(
            request=request,
            audience=audience,
            findings=findings,
            tool_calls=tool_calls,
            risks=risks,
        )

    def _merge_evidence(
        self,
        left: list[ToolEvidence],
        right: list[ToolEvidence],
    ) -> list[ToolEvidence]:
        merged = {item.source: item for item in left}
        for item in right:
            merged.setdefault(item.source, item)
        return sorted(merged.values(), key=lambda item: item.score, reverse=True)

    def _build_insight(
        self,
        topic: str,
        audience: str,
        evidence: list[ToolEvidence],
    ) -> str:
        strongest = evidence[0].excerpt if evidence else "The tool registry did not find a matching note."
        if topic == "single-agent failure":
            return (
                "One agent looks simpler, but it ends up mixing routing, retrieval, synthesis, and recovery in a "
                f"single step. {strongest}"
            )
        if topic == "orchestration":
            return (
                "The orchestrator is valuable because it holds the plan and audience steady while specialists do the "
                f"work. {strongest}"
            )
        if topic == "mcp tools":
            return (
                "MCP-style tools give every agent the same contract, which keeps failures isolated and makes the "
                f"system easier to extend. {strongest}"
            )
        if topic == "yaml pipelines":
            return (
                "YAML makes the orchestration reviewable in pull requests and portable across environments, which "
                f"lands especially well for the {audience} audience. {strongest}"
            )
        if topic == "production deployment":
            return (
                "A production story needs identity, tracing, rollout discipline, and bounded retries before it needs "
                f"clever prompting. {strongest}"
            )
        if topic == "python sdk":
            return (
                "Python developers care that the code stays small: a readable orchestrator, small agent classes, and "
                f"official SDK entry points. {strongest}"
            )
        return strongest

    def _demo_beat(self, topic: str, audience: str) -> str:
        if audience == "malta":
            return f"Connect {topic} to an operable Foundry workflow instead of a notebook-only prototype."
        return f"Connect {topic} to a small, readable Python module."
