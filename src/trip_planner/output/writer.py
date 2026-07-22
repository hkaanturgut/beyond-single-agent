"""Safe markdown writer — normalises filenames and timestamps output files."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from trip_planner.workflow.telemetry import get_logger

_log = get_logger("output.writer")


def _safe_name(text: str) -> str:
    """Convert arbitrary text into a filesystem-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s\-]", "", slug)   # remove non-word chars (except - and space)
    slug = re.sub(r"[\s_]+", "-", slug)     # spaces/underscores to hyphens
    slug = slug.strip("-")
    return slug or "unknown"


def write_brief(markdown: str, destination: str, output_dir: str = "output") -> str:
    """Write *markdown* to a timestamped file and return the resolved path.

    File naming: ``trip-<safe-destination>-<YYYYMMDD-HHMMSS>.md``

    Args:
        markdown:    The full markdown string to write.
        destination: Human-readable destination name (used in the filename).
        output_dir:  Directory to write into; created if it does not exist.

    Returns:
        Absolute path of the written file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    slug = _safe_name(destination)
    filename = f"trip-{slug}-{timestamp}.md"
    filepath = Path(output_dir) / filename

    filepath.write_text(markdown, encoding="utf-8")
    _log.info("Brief saved → %s", filepath.resolve())
    return str(filepath)
