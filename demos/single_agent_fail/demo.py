from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.mcp_tools import MCPToolRegistry


DEFAULT_REQUEST = (
    "Create one answer that explains Foundry visual orchestration, YAML pipelines, MCP tools, "
    "production deployment, and a Python walkthrough for two different audiences."
)

TOPICS = [
    "single-agent failure",
    "orchestration",
    "yaml pipelines",
    "mcp tools",
    "production deployment",
    "python sdk",
]


@dataclass
class FailureReport:
    request: str
    tool_calls_attempted: int
    context_units: int
    context_budget: int
    reasons: list[str]
    attempted_answer: str

    def render(self) -> str:
        lines = [
            "# Single-agent failure demo",
            "",
            f"**Request:** {self.request}",
            f"**Tool calls attempted:** {self.tool_calls_attempted}",
            f"**Context units:** {self.context_units}/{self.context_budget}",
            "",
            "## Why it breaks",
        ]
        lines.extend(f"- {reason}" for reason in self.reasons)
        lines.extend(
            [
                "",
                "## Sample overworked answer",
                self.attempted_answer,
                "",
                "**Takeaway:** the prompt is trying to be an orchestrator, a researcher, and a presenter at the same time.",
            ]
        )
        return "\n".join(lines)


class SingleAgentDemo:
    def __init__(self, registry: MCPToolRegistry, context_budget: int = 110, tool_budget: int = 3) -> None:
        self.registry = registry
        self.context_budget = context_budget
        self.tool_budget = tool_budget

    def run(self, request: str = DEFAULT_REQUEST) -> FailureReport:
        results = [self.registry.search(topic, limit=1) for topic in TOPICS]
        context_blobs = [evidence.excerpt for result in results for evidence in result.evidence]
        context_units = sum(len(blob.split()) for blob in context_blobs)

        reasons = []
        if context_units > self.context_budget:
            reasons.append(
                "The combined research payload no longer fits comfortably in one mental frame, so important details get flattened."
            )
        if len(results) > self.tool_budget:
            reasons.append(
                "The agent needs more tool decisions than its single control loop can explain or retry cleanly."
            )
        reasons.append(
            "One answer is expected to sound like both a platform deep dive and a casual Python talk, so the voice drifts."
        )
        reasons.append(
            "If one tool result is weak, the whole answer becomes shaky because there is no specialist handoff or bounded retry."
        )

        attempted_answer = (
            "Azure AI Foundry supports orchestration, YAML, MCP tools, deployment, and Python. "
            "The answer is technically in the neighborhood, but it is broad, under-evidenced, and tuned for nobody in particular."
        )

        return FailureReport(
            request=request,
            tool_calls_attempted=len(results),
            context_units=context_units,
            context_budget=self.context_budget,
            reasons=reasons,
            attempted_answer=attempted_answer,
        )


if __name__ == "__main__":
    demo = SingleAgentDemo(MCPToolRegistry())
    print(demo.run().render())
