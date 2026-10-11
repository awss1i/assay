"""Check whether a web page works by using every control it renders.

Point assay at a folder. It opens the page in a real browser, measures every
control the page renders, plans cases from what it finds, runs them all, and
reports what broke. You don't write tests, record sessions or keep baseline
images.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from assay.qa import FAILED, PASSED, UNKNOWN, QA, Result
from assay.run import check, look
from assay.surface import Case, Control, Surface, plan

__all__ = ["check", "look", "plan", "QA", "Result", "Case", "Control",
           "Surface", "PASSED", "FAILED", "UNKNOWN"]
try:
    #: Read from the installed package, so `pyproject.toml` is the only place
    #: the version is set.
    __version__ = version("assay-ui")
except PackageNotFoundError:        # running from a source tree
    __version__ = "0+unknown"
