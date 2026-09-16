"""Colour for the terminal, and the rules about when not to use it.

Colour earns its place here for one reason: a run of forty cases with two
failures in it is a wall of identical lines, and the two that matter are
found by scrolling. Dimming what passed and reddening what did not makes the
answer visible without reading a word.

It is off unless stdout is a terminal, so a pipe, a file and a CI log all get
plain text, because escape codes in a captured log are noise nobody asked
for. It
honours `NO_COLOR`, which is the convention, and `FORCE_COLOR` for the case
where the output really is going somewhere that renders it.
"""

from __future__ import annotations

import os
import sys
from typing import Any

#: Eight-colour codes rather than a palette, so they follow whatever theme
#: the reader has chosen. A tool that hardcodes its own greys is unreadable
#: on half the terminals it runs on.
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
    """Wrap text in codes, or hand it back untouched."""
    return f"{''.join(codes)}{text}{OFF}" if on and codes else text
