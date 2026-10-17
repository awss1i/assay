"""Tests for the HTML report. Every label, message and measurement in it comes
from the page, so all of it has to be escaped. None of these need Chromium.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from assay import report
from assay.qa import FAILED, PASSED, UNKNOWN, Result
from assay.surface import Case, Control, Surface

SNEAKY = "<script>alert(1)</script>"


def run_of(*results: Result, surface: Surface = Surface()) -> SimpleNamespace:
    return SimpleNamespace(plan=[r.case for r in results],
                           results={r.case.id: r for r in results},
                           surface=surface)


def test_the_report_counts_every_outcome(tmp_path: Path) -> None:
    run = run_of(
        Result(case=Case(id="C001", what="press Add"), outcome=PASSED),
        Result(case=Case(id="C002", what="press Delete"), outcome=FAILED,
               detail="nothing on the page changed at all"),
        Result(case=Case(id="C003", what="type into Name"), outcome=UNKNOWN))

    page = report.write(run, tmp_path / "out" / "report.html", folder="todo")
    said = page.read_text(encoding="utf-8")

    assert page == tmp_path / "out" / "report.html"
    assert "<b>3</b> cases" in said
    assert "<b>1</b> passed" in said
    assert "<b>1</b> failed" in said
    assert "<b>1</b> not checked" in said
    assert "nothing on the page changed at all" in said


def test_text_from_the_page_is_escaped(tmp_path: Path) -> None:
    run = run_of(
        Result(case=Case(id="C001", what=f"press {SNEAKY}",
                         acts=[{"click": SNEAKY}]),
               outcome=FAILED, detail=f"the page said {SNEAKY}",
               evidence=SNEAKY,
               artifacts={"before": f"{SNEAKY}.png"}),
        surface=Surface(kind="page", controls=[
            Control(kind="button", selector="#go", label=SNEAKY)]))

    said = report.write(run, tmp_path / "report.html",
                        folder=SNEAKY).read_text(encoding="utf-8")

    assert SNEAKY not in said
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in said
