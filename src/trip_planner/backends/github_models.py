"""GitHub Models backend adapter.

Uses the OpenAI-compatible inference endpoint provided by GitHub Models:
    https://models.inference.ai.azure.com

Authentication: a GitHub personal-access token supplied via ``GITHUB_TOKEN``.
"""

from __future__ import annotations

import os
from typing import Optional

from trip_planner.backends.base import BackendAdapter

_GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"


class GitHubModelsBackend(BackendAdapter):
    """Calls GitHub Models using an OpenAI-compatible client."""

    def __init__(self, token: str, model_name: str = "gpt-4o-mini") -> None:
        self._token = token
        self._model_name = model_name
        self._client: Optional[object] = None  # lazy-initialised

    @property
    def name(self) -> str:
        return "github_models"

    def _get_client(self) -> object:
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "The 'openai' package is required for the GitHub Models "
                    "backend.  Install it with: pip install openai>=1.45.0"
                ) from exc

            self._client = AsyncOpenAI(
                base_url=_GITHUB_MODELS_ENDPOINT,
                api_key=self._token,
            )
        return self._client

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        agent_name: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(  # type: ignore[attr-defined]
            model=self._model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    @classmethod
    def from_env(cls) -> "GitHubModelsBackend":
        token = os.getenv("GITHUB_TOKEN", "")
        model = os.getenv("GITHUB_MODEL_NAME", "gpt-4o-mini")
        return cls(token=token, model_name=model)
