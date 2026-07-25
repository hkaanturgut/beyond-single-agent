"""Backend factory — select and instantiate a backend from configuration.

Both backends target the same Azure AI Foundry project:

* ``foundry``         -> :class:`FoundryAgentsBackend` — routes each specialist
  call to its hosted PromptAgent in Foundry Agent Service (the multi-agent
  demo).  Run ``scripts/deploy_agents.py`` once to register the agents.
* ``foundry_models``  -> :class:`FoundryBackend` — direct chat completions
  against the same Foundry model deployment (no hosted agents required).
"""

from __future__ import annotations

from trip_planner.backends.base import BackendAdapter
from trip_planner.backends.foundry import FoundryBackend
from trip_planner.backends.foundry_agents import FoundryAgentsBackend
from trip_planner.config import BackendMode, TripPlannerConfig


def create_backend(cfg: TripPlannerConfig) -> BackendAdapter:
    """Return the appropriate :class:`BackendAdapter` for *cfg*."""
    if cfg.backend == BackendMode.FOUNDRY_MODELS:
        return FoundryBackend(
            project_endpoint=cfg.foundry_project_endpoint,
            model_name=cfg.foundry_model_name,
        )
    return FoundryAgentsBackend(
        project_endpoint=cfg.foundry_project_endpoint,
        model_name=cfg.foundry_model_name,
    )


__all__ = [
    "BackendAdapter",
    "FoundryBackend",
    "FoundryAgentsBackend",
    "create_backend",
]
