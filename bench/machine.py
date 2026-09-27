"""What the numbers were measured on, and how to say how long things took.

A timing without the machine it came from is a number nobody can compare
with their own, so every published duration carries this line beside it.
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


def _spoken(seconds: float) -> str:
    """A duration the way a person would say it."""
    if seconds < 90:
        return f"{seconds:.0f} seconds"
    return f"{seconds / 60:.1f} minutes"
