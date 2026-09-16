"""assay: find out if a generated program actually works.

Point it at a folder. It opens the program in a real browser, measures every
control it renders, derives a test plan from what it finds, drives all of it,
and reports what broke. No tests to write, no baseline images, no recordings.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from assay.qa import FAILED, PASSED, UNKNOWN, QA, Result
from assay.run import check, look
from assay.surface import Case, Control, Surface, plan

__all__ = ["check", "look", "plan", "QA", "Result", "Case", "Control",
           "Surface", "PASSED", "FAILED", "UNKNOWN"]
try:
    #: Read from the installed package rather than written here. The number
    #: was in `pyproject.toml` as well, and a value declared twice is a value
    #: free to disagree with itself the first time either one is bumped.
    __version__ = version("assay-ui")
except PackageNotFoundError:        # running from a source tree
    __version__ = "0+unknown"
