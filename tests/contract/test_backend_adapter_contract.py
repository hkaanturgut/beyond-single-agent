"""Contract tests — backend adapter interface compliance."""

from __future__ import annotations

import pytest

from fakes import FakeBackend

from trip_planner.backends.base import BackendAdapter


def _check_adapter_contract(adapter: BackendAdapter) -> None:
    """Verify that an adapter satisfies the interface contract."""
    assert isinstance(adapter.name, str), "name must return a string"
    assert adapter.name, "name must not be empty"


@pytest.mark.asyncio
class TestBackendAdapterContract:
    async def test_fake_backend_satisfies_contract(self):
        adapter = FakeBackend()
        _check_adapter_contract(adapter)

    async def test_fake_backend_generate_returns_string(self):
        adapter = FakeBackend()
        result = await adapter.generate(
            system_prompt="You are a travel assistant.",
            user_message="Tell me about Lisbon.",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_all_shipped_backends_are_subclasses_of_base(self):
        from trip_planner.backends.foundry import FoundryBackend
        from trip_planner.backends.foundry_agents import FoundryAgentsBackend

        for cls in (FoundryBackend, FoundryAgentsBackend):
            assert issubclass(cls, BackendAdapter), f"{cls} must extend BackendAdapter"

    async def test_fake_backend_generate_accepts_agent_name(self):
        adapter = FakeBackend()
        result = await adapter.generate(
            system_prompt="test",
            user_message="test",
            max_tokens=512,
            agent_name="researcher-agent",
        )
        assert isinstance(result, str)
