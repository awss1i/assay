"""The one sentence something else repeats.

**A filled-in example is an answer, and it gets copied.** This lived in a
skill file as a template for a model to compose, and a live harness run
copied the worked example about assay not being on PATH: a folder name out of
the example, and a cause that was false. It is computed here now, so there is
nothing to fill in.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from assay.cli import one_line
from assay.qa import FAILED, PASSED, UNKNOWN, Result
from assay.surface import Case


def run_of(*results: Result) -> SimpleNamespace:
    return SimpleNamespace(
        plan=[r.case for r in results],
        results={r.case.id: r for r in results})


def case(n: int, what: str) -> Case:
    return Case(id=f"C{n:03d}", what=what)


def test_a_clean_run_is_one_sentence(tmp_path: Path) -> None:
    run = run_of(Result(case=case(1, "press Add"), outcome=PASSED),
                 Result(case=case(2, "press Delete"), outcome=PASSED))

    assert one_line(run, tmp_path, "index.html") == (
        f"assay: checked {tmp_path.name}/index.html, 2 checks, "
        f"nothing flagged.")


def test_a_flagged_case_says_what_it_did_and_what_happened(
        tmp_path: Path) -> None:
    run = run_of(
        Result(case=case(1, "press Add"), outcome=PASSED),
        Result(case=case(2, "press Delete"), outcome=FAILED,
               detail="nothing on the page changed at all"))

    assert one_line(run, tmp_path, "index.html").splitlines() == [
        f"assay: checked {tmp_path.name}/index.html, 2 checks, 1 flagged:",
        "  - press Delete: nothing on the page changed at all"]


def test_a_flagged_case_with_no_detail_still_names_itself(
        tmp_path: Path) -> None:
    """A trailing `: ` reads as a sentence somebody forgot to finish."""
    run = run_of(Result(case=case(1, "press Add"), outcome=FAILED))
    said = one_line(run, tmp_path, "index.html")

    assert said.splitlines()[-1] == "  - press Add"


def test_the_folder_is_named_even_when_the_path_is_a_dot() -> None:
    """`assay .` has no name of its own, and the folder is what tells two
    pages called `index.html` apart."""
    run = run_of(Result(case=case(1, "press Add"), outcome=PASSED))
    said = one_line(run, Path("."), "index.html")

    assert said.startswith(f"assay: checked {Path.cwd().name}/index.html,")


def test_a_case_that_never_ran_is_never_silent(tmp_path: Path) -> None:
    """**A check that did not happen must never read like one that passed.**

    Counting only the failures reports a page as clean on the strength of
    checks that never ran, which is the one thing this whole tool exists to
    stop happening.
    """
    run = run_of(
        Result(case=case(1, "press Add"), outcome=PASSED),
        Result(case=case(2, "press Delete"), outcome=UNKNOWN,
               detail="could not be carried out: timeout"))

    assert one_line(run, tmp_path, "index.html") == (
        f"assay: checked {tmp_path.name}/index.html, 2 checks, "
        f"1 could not be carried out, nothing flagged.")


def test_a_case_with_no_result_at_all_counts_as_not_carried_out(
        tmp_path: Path) -> None:
    """A plan longer than the results is a run that stopped partway."""
    ran = Result(case=case(1, "press Add"), outcome=PASSED)
    run = SimpleNamespace(plan=[ran.case, case(2, "press Delete")],
                          results={ran.case.id: ran})

    said = one_line(run, tmp_path, "index.html")

    assert "1 could not be carried out" in said
