"""Workflow builder primitives — WorkflowBuilder, ConcurrentBuilder, Workflow.

This module provides a local implementation of the orchestration patterns
described in the Microsoft Agent Framework docs:
  - ``WorkflowBuilder``: sequential step chaining
  - ``ConcurrentBuilder``: fan-out with asyncio.gather
  - ``add_multi_selection_edge_group``: conditional routing by selector return value

When the ``agent-framework`` package becomes available on PyPI, the classes
below can be replaced by that library's equivalents.  The calling code in
``runner.py`` uses the same API surface so the swap should be minimal.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from trip_planner.workflow.telemetry import get_logger

_log = get_logger("workflow.builder")

# A step is a coroutine function: async (state) -> state
StepFn = Callable[[Any], Any]


# ---------------------------------------------------------------------------
# ConcurrentBuilder
# ---------------------------------------------------------------------------


class ConcurrentBuilder:
    """Collects fan-out tasks to run in parallel, then returns to WorkflowBuilder."""

    def __init__(self, parent: "WorkflowBuilder") -> None:
        self._parent = parent
        self._tasks: List[Tuple[str, StepFn]] = []

    def add_task(self, name: str, fn: StepFn) -> "ConcurrentBuilder":
        """Register a concurrent task.

        Args:
            name: Human-readable label for logging/tracing.
            fn:   Async callable ``(state) -> result``.  The result is stored
                  on ``state`` using the attribute name derived from *name*
                  (lowercase, spaces replaced by underscores).
        """
        self._tasks.append((name, fn))
        return self

    def done(self) -> "WorkflowBuilder":
        """Finalise the fan-out step and return to the parent builder."""
        self._parent._steps.append(("concurrent", list(self._tasks)))
        return self._parent


# ---------------------------------------------------------------------------
# WorkflowBuilder
# ---------------------------------------------------------------------------


class WorkflowBuilder:
    """Builds a sequential workflow graph with optional concurrent and conditional steps.

    Example::

        workflow = (
            WorkflowBuilder("trip-planner")
            .add_step("parse", parse_step)
            .add_concurrent()
                .add_task("research", researcher_step)
                .add_task("planning", planner_step)
                .add_task("budget", budget_step)
            .done()
            .add_step("aggregate", aggregate_step)
            .add_multi_selection_edge_group(
                "route",
                selector=route_selector,
                branches={"optimize": optimizer_step, "finalize": finalizer_step},
            )
            .build()
        )
        final_state = await workflow.run(initial_state)
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._steps: List[Tuple[str, Any]] = []

    def add_step(self, name: str, fn: StepFn) -> "WorkflowBuilder":
        """Append a sequential step."""
        self._steps.append(("step", (name, fn)))
        return self

    def add_concurrent(self) -> ConcurrentBuilder:
        """Begin a fan-out (concurrent) step.  Call ``.done()`` to return here."""
        return ConcurrentBuilder(parent=self)

    def add_multi_selection_edge_group(
        self,
        name: str,
        selector: Callable[[Any], str],
        branches: Dict[str, StepFn],
    ) -> "WorkflowBuilder":
        """Add conditional routing.

        ``selector(state)`` returns a branch key (e.g. ``"optimize"`` or
        ``"finalize"``).  The matching branch coroutine is called with the
        current state.

        Args:
            name:     Label for tracing.
            selector: ``(state) -> str`` — must return a key in *branches*.
            branches: Mapping of key → async step function.
        """
        self._steps.append(("route", (name, selector, dict(branches))))
        return self

    def build(self) -> "Workflow":
        """Return an executable :class:`Workflow`."""
        return Workflow(self._name, list(self._steps))


# ---------------------------------------------------------------------------
# Workflow (executor)
# ---------------------------------------------------------------------------


class Workflow:
    """An executable workflow produced by :class:`WorkflowBuilder`."""

    def __init__(self, name: str, steps: List[Tuple[str, Any]]) -> None:
        self._name = name
        self._steps = steps

    async def run(self, state: Any) -> Any:
        """Execute all steps in order, mutating *state* at each stage.

        Returns the final state object.
        """
        _log.info("Workflow '%s' starting", self._name)
        for step_type, step_def in self._steps:
            if step_type == "step":
                state = await _run_step(step_def, state)
            elif step_type == "concurrent":
                state = await _run_concurrent(step_def, state)
            elif step_type == "route":
                state = await _run_route(step_def, state)
        _log.info("Workflow '%s' complete", self._name)
        return state


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _run_step(step_def: Tuple[str, StepFn], state: Any) -> Any:
    name, fn = step_def
    _log.debug("  step: %s", name)
    return await fn(state)


async def _run_concurrent(
    tasks: List[Tuple[str, StepFn]], state: Any
) -> Any:
    """Run all tasks concurrently and write results back to state."""
    names = [t[0] for t in tasks]
    fns = [t[1] for t in tasks]
    _log.debug("  fan-out: %s", names)
    results = await asyncio.gather(*[fn(state) for fn in fns])
    # Each fan-out function is expected to write its result onto state directly
    # *and* return it for logging purposes.  We do not overwrite state here;
    # the agent functions own their attribute assignment.
    _log.debug("  fan-in complete: %d results", len(results))
    return state


async def _run_route(step_def: Tuple[str, Any, Dict[str, StepFn]], state: Any) -> Any:
    name, selector, branches = step_def
    key = selector(state)
    _log.info("  route '%s' -> '%s'", name, key)
    if key not in branches:
        available = list(branches.keys())
        raise ValueError(
            f"route selector returned '{key}' but available branches are {available}"
        )
    return await branches[key](state)
