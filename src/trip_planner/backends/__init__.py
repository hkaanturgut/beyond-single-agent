"""Backend factory — select and instantiate a backend from configuration."""

from __future__ import annotations

from trip_planner.backends.base import BackendAdapter
from trip_planner.backends.demo import DemoBackend
from trip_planner.backends.foundry import FoundryBackend
from trip_planner.backends.github_models import GitHubModelsBackend
from trip_planner.config import BackendMode, TripPlannerConfig


def create_backend(cfg: TripPlannerConfig) -> BackendAdapter:
    """Return the appropriate :class:`BackendAdapter` for *cfg*."""
    if cfg.backend == BackendMode.GITHUB_MODELS:
        return GitHubModelsBackend(
            token=cfg.github_token or "",
            model_name=cfg.github_model_name,
        )
    if cfg.backend == BackendMode.FOUNDRY:
        return FoundryBackend(
            project_endpoint=cfg.foundry_project_endpoint or "",
            model_name=cfg.foundry_model_name,
        )
    return DemoBackend()


__all__ = [
    "BackendAdapter",
    "DemoBackend",
    "FoundryBackend",
    "GitHubModelsBackend",
    "create_backend",
]
