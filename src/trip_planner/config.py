"""Configuration loader — reads environment variables and selects the backend.

This project runs entirely on **Azure AI Foundry**.  There is no offline or
demo mode: every run calls the same Foundry project.  Two Foundry backends are
supported, both targeting the same project/model:

    foundry         — hosted multi-agent workflow (5 PromptAgents in Foundry
                      Agent Service, invoked via the Responses API).  [default]
    foundry_models  — direct chat completions against the same Foundry model
                      deployment (no hosted agents required).

Usage::

    from trip_planner.config import TripPlannerConfig
    cfg = TripPlannerConfig.from_env()
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

# Load .env if present (no-op when variables are already set)
load_dotenv(override=False)


class BackendMode(str, Enum):
    """Supported runtime backends — all backed by Azure AI Foundry."""

    FOUNDRY = "foundry"                # hosted multi-agent workflow
    FOUNDRY_MODELS = "foundry_models"  # direct model inference


@dataclass
class TripPlannerConfig:
    """Validated runtime configuration assembled from environment variables."""

    backend: BackendMode

    # ---------- Azure AI Foundry ----------
    foundry_project_endpoint: str
    foundry_model_name: str

    # ---------- Optional MCP ----------
    # Enabled when a remote MCP server URL is configured (MCP_SERVER_URL).
    mcp_enabled: bool

    # ---------- Output ----------
    output_dir: str

    @classmethod
    def from_env(cls) -> "TripPlannerConfig":
        """Build a config from the current environment.

        Raises:
            ValueError: if ``TRIP_BACKEND`` is unknown, or if
                ``FOUNDRY_PROJECT_ENDPOINT`` is not set.  The project is
                Foundry-only, so there is no silent fallback.
        """
        raw = os.getenv("TRIP_BACKEND", BackendMode.FOUNDRY.value).lower().strip()
        try:
            backend = BackendMode(raw)
        except ValueError as exc:
            valid = ", ".join(m.value for m in BackendMode)
            raise ValueError(
                f"Unknown TRIP_BACKEND={raw!r}. Valid options: {valid}."
            ) from exc

        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
        if not endpoint:
            raise ValueError(
                "FOUNDRY_PROJECT_ENDPOINT is required — this project runs on "
                "Azure AI Foundry only.  Set it to your project endpoint, e.g.\n"
                "  https://<resource>.services.ai.azure.com/api/projects/<project>\n"
                "and run `az login` (or configure a service principal) first."
            )

        return cls(
            backend=backend,
            foundry_project_endpoint=endpoint,
            foundry_model_name=os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini"),
            mcp_enabled=bool(os.getenv("MCP_SERVER_URL", "").strip()),
            output_dir=os.getenv("TRIP_OUTPUT_DIR", "output"),
        )
