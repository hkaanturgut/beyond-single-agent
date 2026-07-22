"""trip_planner package — entry point for ``python -m trip_planner``."""

from trip_planner.cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
