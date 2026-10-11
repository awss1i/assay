"""Terminal colour, and when to leave it off.

Colour makes failed cases stand out in a long run. It's off unless the stream
is a terminal, so pipes, files and CI logs get plain text. `NO_COLOR` turns it
off, and otherwise `FORCE_COLOR` turns it on for any stream.
"""

from __future__ import annotations

import os
import sys
from typing import Any

#: The basic eight-colour codes, so the colours follow the terminal's theme.
DIM, RED, GREEN, YELLOW, BOLD, OFF = (
    "\033[2m", "\033[31m", "\033[32m", "\033[33m", "\033[1m", "\033[0m")


def enabled(stream: Any = None) -> bool:
    """Whether to colour what goes to this stream."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = sys.stdout if stream is None else stream
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def paint(text: str, *codes: str, on: bool = True) -> str:
    """Wrap `text` in `codes`, or return it unchanged when `on` is false."""
    return f"{''.join(codes)}{text}{OFF}" if on and codes else text
