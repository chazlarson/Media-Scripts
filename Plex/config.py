"""Config loader for scripts in this directory.

The implementation lives in mediascripts.config so Plex, Kometa, and TMDB
share one class.
"""

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mediascripts.config import Config  # noqa: E402

__all__ = ["Config"]
