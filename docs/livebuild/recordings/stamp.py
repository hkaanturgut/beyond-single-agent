"""Timestamp each line of piped output. Run the source with `python3 -u`."""

import sys
import time

t0 = time.time()
for line in sys.stdin:
    sys.stdout.write(f"{time.time() - t0:.2f}\t{line}")
    sys.stdout.flush()
