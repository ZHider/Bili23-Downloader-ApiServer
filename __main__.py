"""Allow ``python -m api-server`` from the project root."""

import sys
from pathlib import Path

# Ensure this directory is on sys.path so ``serve`` and ``stubs``
# can be found when running from the parent directory.
_home = Path(__file__).resolve().parent
if str(_home) not in sys.path:
    sys.path.insert(0, str(_home))

from serve import main

main()
