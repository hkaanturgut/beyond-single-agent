"""Azure AI Foundry Multi-Agent backend adapter.

Uses ``AIProjectClient`` from ``azure-ai-projects`` (v2+) to call specialist
agents that are registered in Foundry Agent Service via
``scripts/deploy_agents.py``.

Each agent call uses the Responses API with an ``agent_reference``, directing
the request to the specific hosted PromptAgent visible in the Foundry UI.

The Python workflow (WorkflowBuilder + ConcurrentBuilder in workflow/runner.py)
orchestrates concurrent fan-out and conditional routing;  each specialist agent
is invoked through this backend adapter.

Required environment variables
-------------------------------
FOUNDRY_PROJECT_ENDPOINT  — https://<resource>.services.ai.azure.com/api/projects/<proj>
FOUNDRY_MODEL_NAME        — fallback model when no agent_name is given
"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from trip_planner.backends.base import BackendAdapter

# Map the agent's role (system_prompt prefix) to its Foundry agent name.
# This heuristic is now only a *fallback* — specialist agent classes pass an
# explicit ``agent_name`` to ``generate()`` (see ``AGENT_NAME`` in each agent
# module).  The map is retained so ad-hoc callers that don't specify an agent
# name still reach a sensible hosted agent.
_AGENT_NAME_MAP: dict[str, str] = {
    "researcher": "researcher-agent",
    "planner":    "planner-agent",
    "budget":     "budget-agent",
    "optimizer":  "optimizer-agent",
    "finalizer":  "finalizer-agent",
    "writer":     "finalizer-agent",   # finalizer uses "travel writer" label
    "travel":     "finalizer-agent",
    "trip-plan":  "planner-agent",
    "trip optim": "optimizer-agent",
}

_THREAD_POOL = ThreadPoolExecutor(max_workers=8)


def _pick_agent_name(system_prompt: str) -> Optional[str]:
    """Fallback: infer the Foundry agent name from the system prompt.

    Only used when an explicit ``agent_name`` was not supplied to
    :meth:`FoundryAgentsBackend.generate`.
    """
    lower = system_prompt.lower()
    for keyword, agent_name in _AGENT_NAME_MAP.items():
        if keyword in lower:
            return agent_name
    return None


class FoundryAgentsBackend(BackendAdapter):
    """Calls hosted Foundry agents via the Responses API with agent_reference.

    Each specialist agent registered in Foundry Agent Service is invoked by
    name.  The Python multi-agent workflow (WorkflowBuilder + ConcurrentBuilder)
    orchestrates concurrent fan-out and conditional routing — each hosted agent
    runs its focused task, and the Python layer aggregates the results.

    Initialise with ``scripts/deploy_agents.py`` to register the agents before
    running in this backend mode.
    """

    def __init__(self, project_endpoint: str, model_name: str = "gpt-5-mini") -> None:
        self._project_endpoint = project_endpoint
        self._model_name = model_name
        self._project_client: Optional[object] = None
        self._openai_client: Optional[object] = None

    @property
    def name(self) -> str:
        return "foundry_agents"

    def _get_clients(self) -> tuple:
        """Lazily initialise the AIProjectClient and OpenAI Responses client."""
        if self._project_client is None:
            try:
                from azure.ai.projects import AIProjectClient  # type: ignore[import]
                from azure.identity import AzureCliCredential, DefaultAzureCredential  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "azure-ai-projects and azure-identity are required.\n"
                    "Run: pip install azure-ai-projects azure-identity"
                ) from exc

            # Prefer AzureCliCredential for local dev (it uses the https://ai.azure.com
            # scope that the AIProjectClient requires). Fall back to DefaultAzureCredential
            # for CI/CD environments (managed identity, OIDC, etc.).
            try:
                cred = AzureCliCredential()
                cred.get_token("https://ai.azure.com/.default")  # validate
            except Exception:
                cred = DefaultAzureCredential()

            self._project_client = AIProjectClient(
                endpoint=self._project_endpoint,
                credential=cred,
            )
            # get_openai_client() returns a sync openai.OpenAI-compatible client
            # configured to call the Foundry Responses API.
            self._openai_client = self._project_client.get_openai_client()  # type: ignore[attr-defined]

        return self._project_client, self._openai_client

    def _call_agent_sync(
        self,
        agent_name: Optional[str],
        user_message: str,
        max_tokens: int,
    ) -> str:
        """Synchronous Responses API call — run in thread pool for async callers."""
        _, openai_client = self._get_clients()

        extra_body: dict = {}
        if agent_name:
            extra_body = {
                "agent_reference": {
                    "name": agent_name,
                    "type": "agent_reference",
                }
            }

        response = openai_client.responses.create(  # type: ignore[attr-defined]
            model=self._model_name,
            input=user_message,
            max_output_tokens=max_tokens,
            **({"extra_body": extra_body} if extra_body else {}),
        )
        # Extract text from the response output items
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for block in getattr(item, "content", []):
                    text = getattr(block, "text", None)
                    if text:
                        return text
        # Fallback: output_text attribute (present on some SDK versions)
        return getattr(response, "output_text", "") or ""

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        agent_name: Optional[str] = None,
    ) -> str:
        """Invoke a specific hosted Foundry agent via the Responses API.

        Routing is *explicit*: each specialist agent class passes its own
        ``agent_name`` (e.g. ``"researcher-agent"``), so the request is
        dispatched deterministically to the matching hosted PromptAgent.  When
        no ``agent_name`` is supplied, the backend falls back to inferring one
        from *system_prompt* via :func:`_pick_agent_name`.

        The Responses API call runs on a thread pool so the async workflow can
        fan out multiple specialist agents concurrently.
        """
        resolved_name = agent_name or _pick_agent_name(system_prompt)
        # When targeting a hosted agent, its own system instructions take
        # precedence, so only the user content is sent.  Otherwise fold the
        # system prompt into the input for the fallback model call.
        full_input = user_message if resolved_name else f"{system_prompt}\n\n{user_message}"

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _THREAD_POOL,
            self._call_agent_sync,
            resolved_name,
            full_input,
            max_tokens,
        )

    @classmethod
    def from_env(cls) -> "FoundryAgentsBackend":
        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
        model = os.getenv("FOUNDRY_MODEL_NAME", "gpt-5-mini")
        return cls(project_endpoint=endpoint, model_name=model)
