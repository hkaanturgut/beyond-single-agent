from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from agents.domain_agents.research_agent import ResearchAgent, ResearchPacket
from agents.domain_agents.summarizer_agent import SummarizerAgent, SummaryPacket
from tools.mcp_tools import MCPToolRegistry, describe_pipeline


@dataclass
class WorkItem:
    id: str
    objective: str
    owner: str
    status: str = "pending"


@dataclass
class OrchestrationResult:
    request: str
    audience: str
    mode: str
    work_plan: list[WorkItem]
    pipeline_steps: list[str]
    research: ResearchPacket
    summary: SummaryPacket
    trace: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            "# Multi-agent orchestration result",
            "",
            f"**Audience:** {self.audience}",
            f"**Mode:** {self.mode}",
            "",
            "## Work plan",
        ]
        lines.extend(
            f"- `{item.id}` -> {item.owner}: {item.objective} ({item.status})"
            for item in self.work_plan
        )
        lines.extend(["", "## Workflow steps"])
        lines.extend(f"- {step}" for step in self.pipeline_steps)
        lines.extend(["", "## Research findings"])
        lines.extend(f"- {bullet}" for bullet in self.research.bullets())
        lines.extend(["", self.summary.render()])

        if self.trace:
            lines.extend(["", "## Orchestrator trace"])
            lines.extend(f"- {entry}" for entry in self.trace)

        return "\n".join(lines)


class FoundryOrchestrator:
    """Coordinates the domain agents and optionally calls Azure AI Foundry live."""

    def __init__(
        self,
        tool_registry: MCPToolRegistry | None = None,
        research_agent: ResearchAgent | None = None,
        summarizer_agent: SummarizerAgent | None = None,
        workflow_path: str | Path | None = None,
        live_mode: bool = False,
    ) -> None:
        self.tool_registry = tool_registry or MCPToolRegistry()
        self.research_agent = research_agent or ResearchAgent(self.tool_registry)
        self.summarizer_agent = summarizer_agent or SummarizerAgent()
        self.workflow_path = Path(workflow_path or Path(__file__).resolve().parents[1] / "workflows" / "pipeline.yaml")
        self.live_mode = live_mode

    def run(self, request: str, audience: str = "python-toronto") -> OrchestrationResult:
        work_plan = self._plan_work(audience)
        pipeline_steps = describe_pipeline(self.workflow_path)
        trace = [
            f"Accepted request for the {audience} audience.",
            f"Loaded {len(pipeline_steps)} workflow steps from {self.workflow_path.name}.",
        ]

        topics = self._select_topics(request=request, audience=audience)
        research = self.research_agent.investigate(
            request=request,
            topics=topics,
            audience=audience,
        )
        trace.append(f"Research agent returned {len(research.findings)} findings across {len(topics)} topics.")

        summary = self.summarizer_agent.summarize(
            request=request,
            audience=audience,
            research_packet=research,
        )
        trace.append("Summarizer agent turned the findings into an audience-specific talk track.")

        mode = "local-simulation"
        if self.live_mode or os.getenv("ENABLE_LIVE_FOUNDRY") == "1":
            summary.live_foundry_output = self._run_live_foundry(summary, audience)
            trace.append("Executed a live Azure AI Foundry response for the final polish pass.")
            mode = "foundry-live"

        return OrchestrationResult(
            request=request,
            audience=audience,
            mode=mode,
            work_plan=work_plan,
            pipeline_steps=pipeline_steps,
            research=research,
            summary=summary,
            trace=trace,
        )

    def _plan_work(self, audience: str) -> list[WorkItem]:
        items = [
            WorkItem(
                id="classify-request",
                owner="orchestrator",
                objective="Hold the user goal and audience in scope before tools run.",
                status="done",
            ),
            WorkItem(
                id="research-topics",
                owner="research-agent",
                objective="Collect evidence with MCP-style tools instead of stuffing all context into one prompt.",
                status="done",
            ),
            WorkItem(
                id="compose-narrative",
                owner="summarizer-agent",
                objective=f"Convert research into a story that lands for {audience}.",
                status="done",
            ),
        ]
        if self.live_mode or os.getenv("ENABLE_LIVE_FOUNDRY") == "1":
            items.append(
                WorkItem(
                    id="live-polish",
                    owner="orchestrator",
                    objective="Send the structured brief through Azure AI Foundry for a live response.",
                    status="done",
                )
            )
        return items

    def _select_topics(self, request: str, audience: str) -> list[str]:
        request_text = request.lower()
        topics = ["single-agent failure", "orchestration", "mcp tools"]

        if "yaml" in request_text or audience == "malta":
            topics.append("yaml pipelines")
        if "deployment" in request_text or audience == "malta":
            topics.append("production deployment")
        if "python" in request_text or audience == "python-toronto":
            topics.append("python sdk")

        return topics

    def _run_live_foundry(self, summary: SummaryPacket, audience: str) -> str:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        from dotenv import load_dotenv

        load_dotenv()

        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
        model = os.getenv("FOUNDRY_MODEL_NAME")
        if not endpoint or not model:
            raise RuntimeError(
                "Live mode requires FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL_NAME in the environment."
            )

        prompt = summary.to_foundry_prompt(audience=audience)
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            response = openai_client.responses.create(model=model, input=prompt)

        return response.output_text
