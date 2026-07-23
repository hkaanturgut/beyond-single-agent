"""Azure AI Foundry backend adapter.

Uses ``AIProjectClient`` from ``azure-ai-projects`` together with
``DefaultAzureCredential`` from ``azure-identity``.

Required environment variables
-------------------------------
FOUNDRY_PROJECT_ENDPOINT  — e.g. https://<resource>.services.ai.azure.com/api/projects/<proj>
FOUNDRY_MODEL_NAME        — model deployment name (default: gpt-5-mini)
"""

from __future__ import annotations

import os
from typing import Optional

from trip_planner.backends.base import BackendAdapter


class FoundryBackend(BackendAdapter):
    """Calls Azure AI Foundry chat completions via AIProjectClient.

    The client is initialised lazily so that importing this module does not
    fail in environments where ``azure-ai-projects`` is not installed.
    """

    def __init__(self, project_endpoint: str, model_name: str = "gpt-5-mini") -> None:
        self._project_endpoint = project_endpoint
        self._model_name = model_name
        self._chat_client: Optional[object] = None

    @property
    def name(self) -> str:
        return "foundry"

    def _get_chat_client(self) -> object:
        if self._chat_client is None:
            try:
                from azure.ai.projects import AIProjectClient  # type: ignore[import]
                from azure.identity import DefaultAzureCredential  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "The 'azure-ai-projects' and 'azure-identity' packages are "
                    "required for the Foundry backend.  Install them with:\n"
                    "  pip install azure-ai-projects azure-identity"
                ) from exc

            project_client = AIProjectClient(
                endpoint=self._project_endpoint,
                credential=DefaultAzureCredential(),
            )
            # AIProjectClient exposes inference helpers; the exact attribute
            # path may vary across SDK versions — adjust here if needed.
            self._chat_client = project_client.inference.get_chat_completions_client()
        return self._chat_client

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
    ) -> str:
        chat = self._get_chat_client()
        try:
            from azure.ai.inference.models import SystemMessage, UserMessage  # type: ignore[import]

            response = chat.complete(  # type: ignore[attr-defined]
                model=self._model_name,
                messages=[
                    SystemMessage(content=system_prompt),
                    UserMessage(content=user_message),
                ],
                max_tokens=max_tokens,
                temperature=0.4,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(
                f"Foundry chat completion failed: {exc}"
            ) from exc

    @classmethod
    def from_env(cls) -> "FoundryBackend":
        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
        model = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")
        return cls(project_endpoint=endpoint, model_name=model)
