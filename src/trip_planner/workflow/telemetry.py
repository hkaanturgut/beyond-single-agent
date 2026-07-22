"""Simple structured logging / tracing utilities for workflow stages.

This module intentionally avoids external telemetry SDKs so the demo stays
runnable in environments without Application Insights or other monitoring
infrastructure.  Replace or extend as needed for production use.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Generator, Optional

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

_root = logging.getLogger("trip_planner")


def get_logger(name: str) -> logging.Logger:
    """Return a child logger namespaced under ``trip_planner``."""
    return _root.getChild(name)


@contextmanager
def stage_span(logger: logging.Logger, stage_name: str) -> Generator[None, None, None]:
    """Context manager that logs start/end and elapsed time for a named stage."""
    logger.info("▶  %s — starting", stage_name)
    t0 = time.perf_counter()
    try:
        yield
    except Exception as exc:
        logger.error("✗  %s — failed: %s", stage_name, exc)
        raise
    else:
        elapsed = time.perf_counter() - t0
        logger.info("✓  %s — done (%.2fs)", stage_name, elapsed)
