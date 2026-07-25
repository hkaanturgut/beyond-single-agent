"""Backend adapter interface — all concrete backends implement this contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class BackendAdapter(ABC):
    """Minimal contract that every backend must satisfy.

    Concrete implementations live in ``foundry.py`` (direct model inference)
    and ``foundry_agents.py`` (hosted multi-agent), both targeting Azure AI
    Foundry.
    Each adapter wraps one chat-completion provider and exposes a single
    ``generate`` coroutine so that agents remain backend-agnostic.
    """

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        agent_name: Optional[str] = None,
    ) -> str:
        """Send a prompt to the model and return the assistant text.

        Args:
            system_prompt: Instruction text placed in the ``system`` role.
            user_message:  Content placed in the ``user`` role.
            max_tokens:    Upper bound on response length.
            agent_name:    Explicit hosted-agent identifier (e.g.
                ``"researcher-agent"``).  Backends that route to named
                agents (Foundry Agent Service) use this to target a specific
                specialist deterministically instead of inferring it from the
                prompt.  Backends that talk to a single model ignore it.

        Returns:
            The assistant-role response as a plain string.

        Raises:
            RuntimeError: if the backend is unavailable or returns an error.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short human-readable identifier (e.g. ``"foundry_agents"``)."""
