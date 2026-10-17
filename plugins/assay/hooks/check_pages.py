"""A `Stop` hook that checks the pages a turn changed and reports on each one.

The hook prints a line for every page it checks, whether or not assay flagged
anything. If it only reported findings, a clean page would look the same as
assay missing from PATH, assay crashing, or the hook never running. A turn
that changed no page prints nothing.

The hook exits 2 when it reports. A `Stop` hook's output on exit 0 isn't
shown to the model, and exit 2 keeps the turn open and passes the message to
the model, which shows it to the person.

Two guards stop the hook reporting in a loop, and each covers a case the
other misses.

- `stop_hook_active`, which the harness sets on the `Stop` that follows a hook
  holding the turn open. Not every harness sets it.
- A last-run time, written before the pages are checked, so the `Stop` after
  the report finds no newer changes. The file has to survive between hook
  runs, so `pages.clock` picks where it goes, and the hook only holds the
  turn open when the time was written.

The model gets the finished report and is told to print it verbatim, so it
can't reword a finding into a claim that it fixed something. assay doesn't
know what a page is for, so a finding is a place to look, and the person
reading decides what to do.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pages  # noqa: E402

#: Seconds to wait for assay on one page. Long enough for a page with many
#: controls, and short enough that a stuck browser can't hold up the end of a
#: turn for long.
PATIENCE = 240

#: Seconds the hook spends checking pages in all. A harness that cancels a
#: hook throws away what it printed, so this stays shorter than the `timeout`
#: in `hooks.json`, and a page left without time is reported as not checked.
BUDGET = 540

#: The instruction above every report. It's worded to fit any outcome, so it
#: reads correctly above a finding, a clean result or a failure to check.
TELL = ("Print the block below verbatim as your reply, then stop. Don't "
        "change any code because of it.")


def short(page: Path) -> str:
    """The page as `folder/page.html`, the way assay's one-line output names
    it."""
    return f"{page.parent.name}/{page.name}" if page.parent.name else page.name


def summarise(page: Path, patience: float = PATIENCE) -> str:
    """Return assay's one-line report on a page, or why it couldn't check it.

    `page` is the HTML file itself, because pages aren't always called
    `index.html`, and assay checks `index.html` unless `-e` names another
    file. The wording comes from assay's `--one-line`, so the hook and the
    skill print the same sentence.
    """
    where, entry, name = str(page.parent), page.name, short(page)
    try:
        done = subprocess.run(
            ["assay", where, "-e", entry, "--if-page", "--one-line"],
            capture_output=True, text=True, timeout=patience)
    except FileNotFoundError:
        return (f"assay: couldn't check {name} because assay isn't on "
                f"PATH, so nothing was verified.")
    except subprocess.TimeoutExpired:
        return (f"assay: gave up checking {name} after {patience:.0f}s, so "
                f"nothing was verified.")
    except Exception as slipped:
        return (f"assay: couldn't check {name} ({slipped}), so nothing "
                f"was verified.")

    # With `--if-page`, assay prints nothing for a file it can't check, so that
    # page reports nothing. When assay exits 2 because it refused the
    # command, the page reports nothing too.
    if done.returncode == 2:
        return ""
    said = done.stdout.strip()
    if said or done.returncode == 0:
        return said
    # assay prints its findings to stdout when it exits 1, so a failing exit
    # with nothing on stdout means it crashed. Python prints the reason last.
    last = (done.stderr.strip().splitlines() or [""])[-1]
    why = " ".join(last.split())[:200]
    return (f"assay: couldn't check {name} because assay stopped with exit "
            f"code {done.returncode}" + (f" ({why})" if why else "")
            + ", so nothing was verified.")


def main() -> int:
    try:
        said = json.load(sys.stdin)
    except Exception:
        return 0

    # Claude Code sets this on the `Stop` that follows a hook holding the turn
    # open, when the hook mustn't report again. Not every harness sets it, so
    # the last-run time below is a second guard.
    if said.get("stop_hook_active"):
        return 0

    root = Path(said.get("cwd") or ".").resolve()
    clock = pages.clock(said.get("session_id", ""),
                        said.get("scratchpad_dir", ""), root)
    since = pages.last_run(clock)
    # Recorded before checking, so the `Stop` after this report finds nothing
    # newer and doesn't report the same pages again.
    remembered = pages.mark_run(clock)

    try:
        touched = pages.changed(root, since)
    except Exception:
        return 0
    if not touched:
        return 0

    deadline = time.monotonic() + BUDGET
    lines = []
    for page in touched:
        left = min(PATIENCE, deadline - time.monotonic())
        line = summarise(page, left) if left > 0 else (
            f"assay: didn't check {short(page)} because the hook ran out of "
            f"time, so nothing was verified.")
        if line:
            lines.append(line)
    if not lines:
        return 0

    print(TELL, file=sys.stderr)
    print("", file=sys.stderr)
    print("\n".join(lines), file=sys.stderr)
    # Exit 2 shows the report to the model and also leads to another `Stop`.
    # If the last-run time wasn't written, that `Stop` would see the same
    # changes and report them again in a loop, so the hook exits 0 instead and
    # the model doesn't see this report.
    return 2 if remembered else 0


if __name__ == "__main__":
    raise SystemExit(main())
