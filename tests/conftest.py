"""Shared pytest fixtures and path setup."""

from __future__ import annotations

import sys
import os

# Ensure src/ is on the Python path when running pytest from the repo root
_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(_SRC))

# Ensure the tests/ directory itself is importable so `import fakes` works
# regardless of pytest's per-file rootdir insertion.
_TESTS = os.path.dirname(__file__)
if _TESTS not in sys.path:
    sys.path.insert(0, os.path.abspath(_TESTS))
