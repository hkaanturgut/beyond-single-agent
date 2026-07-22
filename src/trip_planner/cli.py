"""CLI entry point for the trip-planner demo.

Usage::

    python -m trip_planner "Plan my 3-day trip to Kyoto in October with budget $1800"

    # Explicit backend override
    TRIP_BACKEND=github_models python -m trip_planner "Plan my 3-day trip to ..."

    # Interactive prompt mode (no argument)
    python -m trip_planner
"""

from __future__ import annotations

import asyncio
import sys

from trip_planner.backends import create_backend
from trip_planner.config import TripPlannerConfig
from trip_planner.models.request import parse_trip_request
from trip_planner.workflow.runner import run_trip_workflow
from trip_planner.workflow.telemetry import get_logger

_log = get_logger("cli")


def _get_prompt_text(argv: list) -> str:
    """Return prompt text from CLI args or stdin."""
    if len(argv) > 1:
        return " ".join(argv[1:])
    # Interactive mode
    print("Trip Planner — enter your request (or Ctrl+C to quit):")
    print('  Example: Plan my 3-day trip to Lisbon in May with budget $2600')
    return input("> ").strip()


def main(argv: list = None) -> int:
    """Main CLI entry point.  Returns exit code."""
    if argv is None:
        argv = sys.argv

    cfg = TripPlannerConfig.from_env()

    if cfg.is_demo_mode:
        print(
            "[trip-planner] Running in DEMO mode — no external backend calls.\n"
            "  Set TRIP_BACKEND=github_models + GITHUB_TOKEN for live responses.\n"
        )
    else:
        print(f"[trip-planner] Backend: {cfg.backend.value}")

    try:
        prompt = _get_prompt_text(argv)
    except KeyboardInterrupt:
        print("\nAborted.")
        return 0

    if not prompt:
        print("Error: no request provided.")
        return 1

    try:
        request = parse_trip_request(prompt)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print(
        f"\n→ Planning trip to {request.destination} in {request.month} "
        f"(budget: ${request.budget_usd:.0f})\n"
    )

    backend = create_backend(cfg)

    try:
        brief = asyncio.run(
            run_trip_workflow(request, backend, output_dir=cfg.output_dir)
        )
    except Exception as exc:
        print(f"\nWorkflow failed: {exc}")
        _log.exception("Unhandled error in workflow")
        return 1

    print(f"\n✓  Brief saved to: {brief.output_path}\n")
    # Print a preview of the first 30 lines
    preview_lines = brief.markdown.splitlines()[:30]
    print("\n".join(preview_lines))
    if len(brief.markdown.splitlines()) > 30:
        print(f"\n... ({len(brief.markdown.splitlines()) - 30} more lines in file)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
