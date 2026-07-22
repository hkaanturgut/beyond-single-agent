"""Contract tests — backend adapter interface compliance."""

from __future__ import annotations

import pytest

from trip_planner.backends.base import BackendAdapter
from trip_planner.backends.demo import DemoBackend


def _check_adapter_contract(adapter: BackendAdapter) -> None:
    """Verify that an adapter satisfies the interface contract."""
    assert isinstance(adapter.name, str), "name must return a string"
    assert adapter.name, "name must not be empty"


@pytest.mark.asyncio
class TestBackendAdapterContract:
    async def test_demo_backend_satisfies_contract(self):
        adapter = DemoBackend()
        _check_adapter_contract(adapter)

    async def test_demo_backend_generate_returns_string(self):
        adapter = DemoBackend()
        result = await adapter.generate(
            system_prompt="You are a travel assistant.",
            user_message="Tell me about Lisbon.",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_demo_backend_name_is_demo(self):
        adapter = DemoBackend()
        assert adapter.name == "demo"

    async def test_all_backends_are_subclasses_of_base(self):
        from trip_planner.backends.demo import DemoBackend
        from trip_planner.backends.github_models import GitHubModelsBackend
        from trip_planner.backends.foundry import FoundryBackend

        for cls in (DemoBackend, GitHubModelsBackend, FoundryBackend):
            assert issubclass(cls, BackendAdapter), f"{cls} must extend BackendAdapter"

    async def test_demo_backend_max_tokens_param_accepted(self):
        adapter = DemoBackend()
        result = await adapter.generate(
            system_prompt="test",
            user_message="test",
            max_tokens=512,
        )
        assert isinstance(result, str)
