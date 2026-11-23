"""Describe the machine a benchmark ran on, summarise timings, and count nouns.

Every published timing names the machine it was measured on, so readers can
compare it with their own.
"""

from __future__ import annotations

import platform
import statistics
import sys
from pathlib import Path
from typing import List


def machine() -> str:
    """One line naming the processor, the system and the browser."""
    cpu = platform.processor() or platform.machine()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(errors="replace").splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    browser = "chromium"
    try:
        from importlib.metadata import version

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            engine = p.chromium.launch()
            browser = (f"Chromium {engine.version}, "
                       f"Playwright {version('playwright')}")
            engine.close()
    except Exception:
        pass
    return (f"{cpu}, {platform.system()} {platform.release()}, "
            f"Python {sys.version.split()[0]}, {browser}")


def timing(seconds: List[float]) -> str:
    """The median, how many finish inside a minute, and the slowest."""
    if not seconds:
        return ""
    slowest = max(seconds)
    return (f"the median is {statistics.median(seconds):.0f} seconds, "
            f"{sum(1 for s in seconds if s < 60)} of {len(seconds)} finish "
            f"inside a minute, and the slowest took {_spoken(slowest)}")


def plural(n: int, word: str) -> str:
    """A count and a noun that takes an s, like "1 flag" or "3 flags"."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _spoken(seconds: float) -> str:
    """A duration in seconds below 90 seconds, and in minutes above."""
    if seconds < 90:
        return f"{seconds:.0f} seconds"
    return f"{seconds / 60:.1f} minutes"
