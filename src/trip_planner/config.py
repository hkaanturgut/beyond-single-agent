"""Configuration loader — reads environment variables and selects the backend.

Usage::

    from trip_planner.config import TripPlannerConfig
    cfg = TripPlannerConfig.from_env()
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

# Load .env if present (no-op when variables are already set)
load_dotenv(override=False)


class BackendMode(str, Enum):
    """Supported runtime backends."""

    GITHUB_MODELS = "github_models"
    FOUNDRY = "foundry"
    DEMO = "demo"  # deterministic template responses — no external calls


@dataclass
class TripPlannerConfig:
    """Validated runtime configuration assembled from environment variables."""

    backend: BackendMode

    # ---------- GitHub Models ----------
    github_token: Optional[str]
    github_model_name: str

    # ---------- Azure AI Foundry ----------
    foundry_project_endpoint: Optional[str]
    foundry_model_name: str

    # ---------- Optional MCP ----------
    mcp_enabled: bool

    # ---------- Output ----------
    output_dir: str

    @classmethod
    def from_env(cls) -> "TripPlannerConfig":
        """Build a config from the current environment.

        Falls back to ``BackendMode.DEMO`` when the requested backend lacks
        the required credentials so the demo never crashes on missing secrets.
        """
        raw = os.getenv("TRIP_BACKEND", "demo").lower().strip()
        try:
            requested = BackendMode(raw)
        except ValueError:
            requested = BackendMode.DEMO

        # Auto-downgrade to demo when credentials are absent
        backend = _resolve_backend(requested)

        return cls(
            backend=backend,
            github_token=os.getenv("GITHUB_TOKEN"),
            github_model_name=os.getenv("GITHUB_MODEL_NAME", "gpt-4o-mini"),
            foundry_project_endpoint=os.getenv("FOUNDRY_PROJECT_ENDPOINT"),
            foundry_model_name=os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini"),
            mcp_enabled=os.getenv("MCP_ENABLED", "false").lower() == "true",
            output_dir=os.getenv("TRIP_OUTPUT_DIR", "output"),
        )

    @property
    def is_demo_mode(self) -> bool:
        return self.backend == BackendMode.DEMO


def _resolve_backend(requested: BackendMode) -> BackendMode:
    """Return the *effective* backend, falling back to DEMO when creds are missing."""
    if requested == BackendMode.GITHUB_MODELS:
        if os.getenv("GITHUB_TOKEN"):
            return BackendMode.GITHUB_MODELS
        return BackendMode.DEMO

    if requested == BackendMode.FOUNDRY:
        if os.getenv("FOUNDRY_PROJECT_ENDPOINT"):
            return BackendMode.FOUNDRY
        return BackendMode.DEMO

    return BackendMode.DEMO
