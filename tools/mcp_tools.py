from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class KnowledgeDocument:
    identifier: str
    title: str
    tags: tuple[str, ...]
    excerpt: str
    body: str

    def combined_text(self) -> str:
        tag_text = " ".join(self.tags)
        return f"{self.title} {self.excerpt} {self.body} {tag_text}".lower()


@dataclass(frozen=True)
class ToolEvidence:
    source: str
    excerpt: str
    tags: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    query: str
    summary: str
    evidence: list[ToolEvidence]
    latency_ms: int


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    query: str
    result_count: int


DEFAULT_DOCUMENTS = [
    KnowledgeDocument(
        identifier="single-agent-failure",
        title="Why single agents break down",
        tags=("single-agent failure", "context", "retries", "specialization"),
        excerpt="One prompt can answer a question, but it struggles when retrieval, planning, repair, and audience adaptation all compete for the same context budget.",
        body="Use this note when you want to show why a single agent can look impressive in a toy notebook but collapse once you add tool calls, retries, and multiple stakeholders.",
    ),
    KnowledgeDocument(
        identifier="foundry-visual-orchestrator",
        title="Foundry visual orchestration",
        tags=("orchestration", "foundry", "visual-orchestrator", "routing"),
        excerpt="A visual orchestrator makes routing, approvals, and parallel branches visible to the team instead of hiding them in one giant prompt.",
        body="This lands well in the Malta talk because it makes the architecture feel operable: you can point to handoffs, gate risky actions, and connect the graph to deployment workflows.",
    ),
    KnowledgeDocument(
        identifier="yaml-pipelines",
        title="Workflow YAML as a review surface",
        tags=("yaml pipelines", "workflow", "reviewability", "promotion"),
        excerpt="YAML keeps the orchestration portable, reviewable, and environment-aware, which matters when the same demo becomes a shared team asset.",
        body="The key point is not that YAML is glamorous. The point is that a workflow file survives code review, environment promotion, and rollback much better than an untracked prompt sitting in one developer's shell history.",
    ),
    KnowledgeDocument(
        identifier="mcp-tools",
        title="MCP tools as stable contracts",
        tags=("mcp tools", "tooling", "contracts", "grounding"),
        excerpt="MCP lets agents share the same tool contracts for search, lookup, and action, which keeps the orchestration layer simpler and makes failures easier to isolate.",
        body="A good demo angle is that the research agent can depend on search semantics while the summarizer stays tool-agnostic. That separation is hard to preserve when one agent owns every responsibility.",
    ),
    KnowledgeDocument(
        identifier="production-deployment",
        title="Production deployment checklist",
        tags=("production deployment", "identity", "tracing", "rollback", "approvals"),
        excerpt="Production-grade agent systems need managed identity, traces, bounded retries, evaluation, and rollout gates before they need more prompt cleverness.",
        body="This is the bridge from demo to platform story: once an agent can call tools, someone has to own secrets, observability, deployment approval, and blast-radius control.",
    ),
    KnowledgeDocument(
        identifier="python-sdk",
        title="Python SDK walkthrough",
        tags=("python sdk", "azure-ai-projects", "defaultazurecredential", "code-tour"),
        excerpt="The Python story works when the code stays small: `AIProjectClient`, `DefaultAzureCredential`, a compact orchestrator, and domain agents with obvious responsibilities.",
        body="For the Python Toronto audience, emphasize that multi-agent does not require a huge framework. It requires a few well-named classes and a clean interface to tools.",
    ),
]


class MCPToolRegistry:
    """Small in-memory registry that behaves like a stable MCP integration surface."""

    def __init__(self, documents: list[KnowledgeDocument] | None = None) -> None:
        self.documents = documents or DEFAULT_DOCUMENTS

    def available_tools(self) -> list[str]:
        return ["search", "lookup"]

    def run(self, tool_name: str, query: str, limit: int = 3) -> ToolResult:
        if tool_name == "search":
            return self.search(query=query, limit=limit)
        if tool_name == "lookup":
            return self.lookup(topic=query, limit=limit)
        raise ValueError(f"Unsupported tool: {tool_name}")

    def search(self, query: str, limit: int = 3) -> ToolResult:
        query_tokens = set(_tokenize(query))
        ranked: list[ToolEvidence] = []

        for document in self.documents:
            document_tokens = set(_tokenize(document.combined_text()))
            title_tokens = set(_tokenize(document.title))
            tag_tokens = set(_tokenize(" ".join(document.tags)))
            overlap = query_tokens & document_tokens
            if not overlap:
                continue
            score = float(len(overlap)) / max(len(query_tokens), 1)
            if query_tokens <= tag_tokens or query_tokens <= title_tokens:
                score += 1.0
            ranked.append(
                ToolEvidence(
                    source=document.title,
                    excerpt=document.excerpt,
                    tags=document.tags,
                    score=round(score, 2),
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        evidence = ranked[:limit]
        summary = (
            "Top matches: " + ", ".join(item.source for item in evidence)
            if evidence
            else "No matching notes were found in the local MCP knowledge base."
        )
        return ToolResult(
            tool_name="search",
            query=query,
            summary=summary,
            evidence=evidence,
            latency_ms=18 + len(query_tokens) * 3,
        )

    def lookup(self, topic: str, limit: int = 1) -> ToolResult:
        topic_tokens = set(_tokenize(topic))
        evidence: list[ToolEvidence] = []

        for document in self.documents:
            tag_tokens = set(_tokenize(" ".join(document.tags)))
            if topic_tokens <= tag_tokens or topic_tokens <= set(_tokenize(document.title)):
                evidence.append(
                    ToolEvidence(
                        source=document.title,
                        excerpt=document.body,
                        tags=document.tags,
                        score=2.0,
                    )
                )

        if not evidence:
            fallback = self.search(query=topic, limit=limit)
            return ToolResult(
                tool_name="lookup",
                query=topic,
                summary=fallback.summary,
                evidence=fallback.evidence[:limit],
                latency_ms=fallback.latency_ms,
            )

        return ToolResult(
            tool_name="lookup",
            query=topic,
            summary="Direct topic lookup succeeded.",
            evidence=evidence[:limit],
            latency_ms=12 + len(topic_tokens) * 2,
        )


def load_pipeline_template(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def describe_pipeline(path: str | Path) -> list[str]:
    pipeline = load_pipeline_template(path)
    steps = pipeline.get("workflow", [])
    return [
        f"{step['id']} -> {step['agent']}: {step['action']}"
        for step in steps
    ]


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())
