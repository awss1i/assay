"""Tests for the plugin's hook: where it records its last run, the two guards
that stop it holding a turn open in a loop, and what it reports for a page.

The hook exits 2 to show its result to the model, which also starts another
`Stop` round. That's only safe while the hook can record that it already ran.
"""

from __future__ import annotations

import importlib.util
import json
import os
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
    """Inside `.git` the file lasts between runs and never shows up in
    `git status`."""
    (tmp_path / ".git").mkdir()

    where = pages.clock("s1", "", tmp_path)

    assert where.parent == tmp_path / ".git"


def test_the_clock_finds_the_repository_from_a_subfolder(
        tmp_path: Path) -> None:
    """A harness can run in any folder of a repository. The clock still goes
    in the repository's `.git`, not into the project as a dotfile."""
    (tmp_path / ".git").mkdir()
    deep = tmp_path / "site" / "pages"
    deep.mkdir(parents=True)

    where = pages.clock("s1", "", deep)

    assert where.parent == tmp_path / ".git"


def test_the_clock_follows_a_worktree_to_its_git_folder(
        tmp_path: Path) -> None:
    """In a worktree or submodule `.git` is a file naming the real folder."""
    real = tmp_path / "main" / ".git" / "worktrees" / "wt"
    real.mkdir(parents=True)
    tree = tmp_path / "wt"
    tree.mkdir()
    (tree / ".git").write_text(f"gitdir: {real}\n", encoding="utf-8")

    where = pages.clock("s1", "", tree)

    assert where.parent == real


def test_a_relative_gitdir_is_read_from_the_folder_holding_it(
        tmp_path: Path) -> None:
    real = tmp_path / "main" / ".git" / "modules" / "sub"
    real.mkdir(parents=True)
    sub = tmp_path / "main" / "sub"
    sub.mkdir()
    (sub / ".git").write_text("gitdir: ../.git/modules/sub\n",
                              encoding="utf-8")

    where = pages.clock("s1", "", sub)

    assert where.parent.resolve() == real.resolve()


def test_a_folder_that_is_not_a_repository_gets_one_dotfile(
        tmp_path: Path) -> None:
    """Outside a repository the hook writes one dotfile in the workspace, not
    the temp directory. Some harnesses give each hook run a private `/tmp`
    that's cleared between runs, so the hook would never remember running.
    """
    where = pages.clock("s1", "", tmp_path)

    assert where == tmp_path / ".assay-last-run"


def test_one_file_per_folder_rather_than_one_per_session(
        tmp_path: Path) -> None:
    """Sessions share one dotfile so the hook doesn't add a file to the
    project for every session. A second session in the same folder may skip
    a report as a result."""
    assert pages.clock("s1", "", tmp_path) == pages.clock("s2", "", tmp_path)


def test_the_clock_says_when_it_could_not_be_written(tmp_path: Path) -> None:
    """`mark_run` returns False when it can't write the file, so the hook
    knows not to hold the turn open."""
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
    """A stand-in for stdin, which carries the hook's JSON payload."""

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
    """The harness sets `stop_hook_active` on the `Stop` that follows a `Stop`
    hook holding the turn open, so the hook exits 0 silently then."""
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
    """When `mark_run` fails, the hook still prints its result but exits 0,
    so the harness doesn't run it again in a loop."""
    check = load("check_pages")
    (tmp_path / "index.html").write_text("<!doctype html><body>hi")
    monkeypatch.setattr(check.pages, "mark_run", lambda path: False)
    monkeypatch.setattr(check, "summarise",
                        lambda page, patience=0: "assay: checked it.")

    code = run_hook({"cwd": str(tmp_path), "session_id": "s"}, check)

    assert code == 0
    assert "assay: checked it." in capsys.readouterr().err


def fake_assay(tmp_path: Path, monkeypatch, body: str) -> None:
    """Put an `assay` on PATH that runs `body`, a few lines of Python."""
    where = tmp_path / "bin"
    where.mkdir()
    exe = where / "assay"
    exe.write_text(f"#!{sys.executable}\nimport sys\n{body}\n",
                   encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{where}{os.pathsep}{os.environ['PATH']}")


def a_page(tmp_path: Path) -> Path:
    page = tmp_path / "site" / "index.html"
    page.parent.mkdir()
    page.write_text("<!doctype html><body><button>Go</button>")
    return page


def test_a_crash_is_reported_rather_than_silent(
        tmp_path: Path, monkeypatch) -> None:
    """assay prints its findings when it exits 1, so exit 1 with nothing on
    stdout is a crash. Saying nothing would look like a clean page."""
    check = load("check_pages")
    fake_assay(tmp_path, monkeypatch,
               "print('Traceback (most recent call last):', file=sys.stderr)\n"
               "print(\"ModuleNotFoundError: No module named 'assay'\", "
               "file=sys.stderr)\n"
               "sys.exit(1)")

    said = check.summarise(a_page(tmp_path))

    assert said == ("assay: couldn't check site/index.html because assay "
                    "stopped with exit code 1 (ModuleNotFoundError: No module "
                    "named 'assay'), so nothing was verified.")


def test_findings_are_passed_on_as_assay_wrote_them(
        tmp_path: Path, monkeypatch) -> None:
    check = load("check_pages")
    fake_assay(tmp_path, monkeypatch,
               "print('assay: checked site/index.html, 2 checks, 1 flagged:')\n"
               "print('  - press Go: nothing on the page changed at all')\n"
               "sys.exit(1)")

    said = check.summarise(a_page(tmp_path))

    assert said.splitlines() == [
        "assay: checked site/index.html, 2 checks, 1 flagged:",
        "  - press Go: nothing on the page changed at all"]


def test_a_file_assay_cannot_check_says_nothing(
        tmp_path: Path, monkeypatch) -> None:
    """With `--if-page`, assay exits 0 and prints nothing for a file that
    isn't a checkable page, and the hook passes that silence on."""
    check = load("check_pages")
    fake_assay(tmp_path, monkeypatch, "sys.exit(0)")

    assert check.summarise(a_page(tmp_path)) == ""


def test_a_page_left_without_time_is_reported_as_not_checked(
        tmp_path: Path, capsys, monkeypatch) -> None:
    check = load("check_pages")
    a_page(tmp_path)
    monkeypatch.setattr(check, "BUDGET", 0)

    def never(page, patience=0):
        raise AssertionError("assay was started with no time left")

    monkeypatch.setattr(check, "summarise", never)

    code = run_hook({"cwd": str(tmp_path), "session_id": "s"}, check)

    assert code == 2
    assert ("assay: didn't check site/index.html because the hook ran out of "
            "time, so nothing was verified.") in capsys.readouterr().err


def test_the_hook_finishes_inside_its_own_timeout() -> None:
    """A harness that cancels a hook throws away what it printed, so the
    hook's time budget has to end before the `timeout` in `hooks.json`."""
    check = load("check_pages")
    said = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
    timeout = said["hooks"]["Stop"][0]["hooks"][0]["timeout"]

    assert check.PATIENCE <= check.BUDGET < timeout
