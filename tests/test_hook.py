"""The hook's memory, and the two guards that stop it looping.

The plugin's hook holds a turn open so its line reaches the model, and what
makes that safe is being able to remember having done it. Both halves of that
have been measured failing on a live harness, so both are asserted here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "assay" / "hooks"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


pages = load("pages")


def test_the_clock_prefers_a_scratchpad_the_harness_gave_it(
        tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    work = tmp_path / "work"
    work.mkdir()

    where = pages.clock("s1", str(scratch), work)

    assert where.parent == scratch


def test_the_clock_hides_in_git_when_there_is_one(tmp_path: Path) -> None:
    """Durable in every harness, and git never shows what is in there."""
    (tmp_path / ".git").mkdir()

    where = pages.clock("s1", "", tmp_path)

    assert where.parent == tmp_path / ".git"


def test_a_folder_that_is_not_a_repository_gets_one_dotfile(
        tmp_path: Path) -> None:
    """**The temp directory is the obvious place and it is the wrong one.**

    A harness may run a hook with a private `/tmp`: the file is written,
    reads back inside the same process, and is gone by the next invocation.
    That bought eleven identical reports in three minutes. The workspace is
    the one place every harness can write and nothing clears.
    """
    where = pages.clock("s1", "", tmp_path)

    assert where == tmp_path / ".assay-last-run"


def test_one_file_per_folder_rather_than_one_per_session(
        tmp_path: Path) -> None:
    """Accumulating a file per session in somebody's project is worse than
    the report a second session in one folder might skip."""
    assert pages.clock("s1", "", tmp_path) == pages.clock("s2", "", tmp_path)


def test_the_clock_says_when_it_could_not_be_written(tmp_path: Path) -> None:
    """**The caller needs this answer, and for a while it was thrown away.**

    Swallowing the failure made a hook whose memory did not work behave
    exactly like one whose memory did, and the only symptom was the loop.
    """
    assert pages.mark_run(tmp_path / "clock") is True
    assert pages.mark_run(tmp_path / "clock" / "under-a-file") is False


def test_the_clock_round_trips(tmp_path: Path) -> None:
    where = tmp_path / "clock"
    pages.mark_run(where)

    assert pages.last_run(where) > 0


def test_no_clock_reads_as_far_enough_back_to_catch_this_turn(
        tmp_path: Path) -> None:
    import time

    was = pages.last_run(tmp_path / "never-written")

    assert time.time() - pages.FIRST_LOOK - 5 < was <= time.time()


class Said:
    """Stdin, which is how a hook is handed its payload."""

    def __init__(self, text: str) -> None:
        self.text = text

    def read(self) -> str:
        return self.text


def run_hook(payload: dict, check=None) -> int:
    check = check or load("check_pages")
    real, sys.stdin = sys.stdin, Said(json.dumps(payload))
    try:
        return check.main()
    finally:
        sys.stdin = real


def test_the_harness_loop_guard_is_honoured(tmp_path: Path, capsys) -> None:
    """`stop_hook_active` is set on exactly the `Stop` that follows a `Stop`
    hook holding the turn open, which is the moment this must not speak."""
    (tmp_path / "index.html").write_text("<!doctype html><body>hi")

    code = run_hook({"cwd": str(tmp_path), "session_id": "s",
                     "stop_hook_active": True})

    assert code == 0
    assert capsys.readouterr().err == ""


def test_a_turn_that_touched_no_page_says_nothing(
        tmp_path: Path, capsys) -> None:
    (tmp_path / "notes.txt").write_text("nothing to do with a page")

    code = run_hook({"cwd": str(tmp_path), "session_id": "s"})

    assert code == 0
    assert capsys.readouterr().err == ""


def test_it_will_not_hold_a_turn_open_it_cannot_remember_holding(
        tmp_path: Path, capsys, monkeypatch) -> None:
    """Unheard once is recoverable. A loop is not."""
    check = load("check_pages")
    (tmp_path / "index.html").write_text("<!doctype html><body>hi")
    monkeypatch.setattr(check.pages, "mark_run", lambda path: False)
    monkeypatch.setattr(check, "summarise", lambda page: "assay: checked it.")

    code = run_hook({"cwd": str(tmp_path), "session_id": "s"}, check)

    assert code == 0
    assert "assay: checked it." in capsys.readouterr().err
