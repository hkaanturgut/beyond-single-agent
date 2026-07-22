from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.orchestrator import FoundryOrchestrator
from tools.mcp_tools import MCPToolRegistry


DEFAULT_REQUESTS = {
    "malta": (
        "Show how Azure AI Foundry visual orchestration, YAML pipelines, MCP tools, and production "
        "deployment practices fit together in one multi-agent demo."
    ),
    "python-toronto": (
        "Explain to a casual Python audience why an orchestrator plus focused domain agents is easier "
        "to reason about than one super-agent."
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-agent orchestration demo.")
    parser.add_argument(
        "--audience",
        choices=sorted(DEFAULT_REQUESTS),
        default="python-toronto",
        help="Which talk framing to generate.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call a real Azure AI Foundry project instead of staying in local simulation mode.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()
    args = parse_args()

    orchestrator = FoundryOrchestrator(
        tool_registry=MCPToolRegistry(),
        workflow_path=REPO_ROOT / "workflows" / "pipeline.yaml",
        live_mode=args.live,
    )

    result = orchestrator.run(
        request=DEFAULT_REQUESTS[args.audience],
        audience=args.audience,
    )
    print(result.render())

