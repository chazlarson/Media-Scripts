"""Helpers for scripts in this directory.

The implementation lives in mediascripts.helpers so Plex, Kometa, and TMDB
share one module. The Plex auth-file behavior (baseurl or url) is that copy.
"""

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mediascripts import helpers as _helpers  # noqa: E402

_public = {
    name: value
    for name, value in vars(_helpers).items()
    if not name.startswith("_")
}
globals().update(_public)
__all__ = sorted(_public)
