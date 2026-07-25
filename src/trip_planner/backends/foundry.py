"""Azure AI Foundry backend adapter — direct model inference.

Calls the Foundry model deployment directly via the OpenAI-compatible client
returned by ``AIProjectClient.get_openai_client()`` (azure-ai-projects v2+).
This is the same Foundry project used by :class:`FoundryAgentsBackend`; the
difference is that this backend talks to the model deployment directly rather
than routing through hosted PromptAgents.

Required environment variables
-------------------------------
FOUNDRY_PROJECT_ENDPOINT  — e.g. https://<resource>.services.ai.azure.com/api/projects/<proj>
FOUNDRY_MODEL_NAME        — model deployment name (default: gpt-5-mini)
"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from trip_planner.backends.base import BackendAdapter

_THREAD_POOL = ThreadPoolExecutor(max_workers=8)


class FoundryBackend(BackendAdapter):
    """Direct chat completions against an Azure AI Foundry model deployment.

    The OpenAI-compatible client is initialised lazily so that importing this
    module does not fail when ``azure-ai-projects`` is not installed.
    """

    def __init__(self, project_endpoint: str, model_name: str = "gpt-5-mini") -> None:
        self._project_endpoint = project_endpoint
        self._model_name = model_name
        self._openai_client: Optional[object] = None

    @property
    def name(self) -> str:
        return "foundry"

    def _get_client(self) -> object:
        if self._openai_client is None:
            try:
                from azure.ai.projects import AIProjectClient  # type: ignore[import]
                from azure.identity import (  # type: ignore[import]
                    AzureCliCredential,
                    DefaultAzureCredential,
                )
            except ImportError as exc:
                raise RuntimeError(
                    "The 'azure-ai-projects' and 'azure-identity' packages are "
                    "required for the Foundry backend.  Install them with:\n"
                    "  pip install azure-ai-projects azure-identity"
                ) from exc

            # Prefer AzureCliCredential for local dev (correct https://ai.azure.com
            # scope); fall back to DefaultAzureCredential for CI/CD (OIDC / MI).
            try:
                cred = AzureCliCredential()
                cred.get_token("https://ai.azure.com/.default")
            except Exception:
                cred = DefaultAzureCredential()

            project_client = AIProjectClient(
                endpoint=self._project_endpoint,
                credential=cred,
            )
            self._openai_client = project_client.get_openai_client()  # type: ignore[attr-defined]
        return self._openai_client

    def _complete_sync(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        client = self._get_client()
        response = client.chat.completions.create(  # type: ignore[attr-defined]
            model=self._model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        agent_name: Optional[str] = None,
    ) -> str:
        """Call the Foundry model directly (``agent_name`` is ignored here)."""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                _THREAD_POOL,
                self._complete_sync,
                system_prompt,
                user_message,
                max_tokens,
            )
        except Exception as exc:
            raise RuntimeError(f"Foundry chat completion failed: {exc}") from exc

    @classmethod
    def from_env(cls) -> "FoundryBackend":
        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
        model = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")
        return cls(project_endpoint=endpoint, model_name=model)
