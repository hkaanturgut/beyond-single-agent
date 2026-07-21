from __future__ import annotations

from dataclasses import dataclass, field

from agents.domain_agents.research_agent import ResearchPacket


@dataclass
class SummarySection:
    title: str
    body: str


@dataclass
class SummaryPacket:
    audience: str
    headline: str
    sections: list[SummarySection]
    closing: str
    live_foundry_output: str | None = None
    supporting_points: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"# {self.headline}", ""]
        for section in self.sections:
            lines.extend([f"## {section.title}", section.body, ""])
        if self.supporting_points:
            lines.append("## Supporting points")
            lines.extend(f"- {point}" for point in self.supporting_points)
            lines.append("")
        if self.live_foundry_output:
            lines.extend(["## Live Foundry response", self.live_foundry_output, ""])
        lines.append(f"**Close:** {self.closing}")
        return "\n".join(lines)

    def to_foundry_prompt(self, audience: str) -> str:
        sections = "\n".join(f"- {section.title}: {section.body}" for section in self.sections)
        supporting = "\n".join(f"- {point}" for point in self.supporting_points)
        return (
            f"You are preparing a concise talk track for the {audience} audience.\n"
            f"Headline: {self.headline}\n"
            f"Sections:\n{sections}\n"
            f"Supporting points:\n{supporting}\n"
            f"Closing: {self.closing}\n"
            "Return a polished speaker-ready paragraph with a practical tone."
        )


class SummarizerAgent:
    """Turns structured findings into a narrative that fits the room."""

    def summarize(
        self,
        request: str,
        audience: str,
        research_packet: ResearchPacket,
    ) -> SummaryPacket:
        if audience == "malta":
            return self._for_malta(request, research_packet)
        return self._for_python_toronto(request, research_packet)

    def _for_malta(self, request: str, research_packet: ResearchPacket) -> SummaryPacket:
        finding_map = {finding.topic: finding for finding in research_packet.findings}
        sections = [
            SummarySection(
                title="Why orchestration needs a control plane",
                body=finding_map["orchestration"].insight,
            ),
            SummarySection(
                title="Why the workflow belongs in YAML too",
                body=finding_map["yaml pipelines"].insight,
            ),
            SummarySection(
                title="Why MCP tools help in production",
                body=finding_map["mcp tools"].insight,
            ),
            SummarySection(
                title="What makes the demo production-shaped",
                body=finding_map["production deployment"].insight,
            ),
        ]
        return SummaryPacket(
            audience="malta",
            headline="Azure AI Foundry turns multi-agent demos into systems you can reason about, review, and deploy.",
            sections=sections,
            supporting_points=[
                finding_map["orchestration"].recommended_demo_beat,
                finding_map["yaml pipelines"].recommended_demo_beat,
                finding_map["production deployment"].recommended_demo_beat,
            ],
            closing="A visually explainable graph plus code-backed YAML is how you move from clever prompt to team-owned workflow.",
        )

    def _for_python_toronto(self, request: str, research_packet: ResearchPacket) -> SummaryPacket:
        finding_map = {finding.topic: finding for finding in research_packet.findings}
        sections = [
            SummarySection(
                title="Why one agent becomes a maintenance problem",
                body=finding_map["single-agent failure"].insight,
            ),
            SummarySection(
                title="What the orchestrator class buys you",
                body=finding_map["orchestration"].insight,
            ),
            SummarySection(
                title="Why small domain agents are easier to trust",
                body=finding_map["python sdk"].insight,
            ),
            SummarySection(
                title="Why tools should stay behind a stable interface",
                body=finding_map["mcp tools"].insight,
            ),
        ]
        return SummaryPacket(
            audience="python-toronto",
            headline="A tiny orchestrator and two focused agents are easier to explain than one giant all-knowing prompt.",
            sections=sections,
            supporting_points=[
                finding_map["single-agent failure"].recommended_demo_beat,
                finding_map["python sdk"].recommended_demo_beat,
                finding_map["mcp tools"].recommended_demo_beat,
            ],
            closing="The win is not magical autonomy; it is explicit responsibilities that make the Python code and the runtime behavior easier to follow.",
        )
