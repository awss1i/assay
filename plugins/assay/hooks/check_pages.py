"""Check the pages this turn touched, and always say what happened.

**It speaks every time it checks something, clean or not.** Reporting only on
a finding was the first design and it was wrong in a way that took three live
tests to see: a hook that says nothing when the page is fine says exactly the
same nothing when assay is missing, when it crashed, and when the hook never
fired at all. Four states, one silence, and no way to tell a working check
from an absent one. A check that did not happen must never read like one that
passed.

So a turn that touched a page always ends with one line. A turn that touched
no page says nothing, because there is nothing to report and no ambiguity in
saying so.

**Exit 2, and the sentence arrives finished.** On a `Stop` hook exit 0 means
the text is filed where nobody reads it: the turn has already ended, and the
model has no reason to look. Exit 2 holds the turn open and puts the message
in front of the model, which is the only channel that reaches a person.

**Two guards stop it looping, and it needs both.** The clock is moved forward
the moment the scan happens, so the step this forces is measured from *now*:
printing a line changes no files, so the `Stop` that ends that step finds
nothing changed and exits 0. Beside it sits `stop_hook_active`, which the
harness sets on exactly that `Stop`.

Either one alone has been measured failing. `stop_hook_active` is not filled
in everywhere. And a clock is only a clock where it survives the process that
wrote it: a hook running with a private `/tmp` writes one, reads it back, and
finds it gone next time, which bought eleven identical reports in three
minutes. So the clock is kept where the work is, and holding the turn open at
all is conditional on having somewhere to record that it happened.

The model is handed the whole line rather than asked to compose one. A
template something is asked to reproduce is a template that drifts, and the
drift here would be into *"I have fixed it"*, which is the one thing a finding
must not cause. assay has not been told what the page is for, so what it found
is a place to look and the judgement stays with whoever is reading.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pages  # noqa: E402

#: Long enough for a page with a lot of controls, short enough that a wedged
#: browser cannot sit on the end of a turn. The hook's own ceiling is 600.
PATIENCE = 240

#: Said the same way whatever the outcome, because the alternative is a
#: preamble that talks about defects above a line reporting that nothing could
#: be checked at all.
TELL = ("Print the block below verbatim as your reply, then stop. Do not "
        "change any code in response to it.")


def summarise(page: Path) -> str:
    """One line about one page, whatever happened to it.

    `page` is the file, because the name is the model's to choose and assay
    defaults to `index.html`. A page called `todo.html` is checked by telling
    assay so, not by hoping.

    **The sentence is assay's, not this file's.** It used to be assembled
    here, out of numbers scraped from assay's own report: two parsers, a
    format to keep in step, and a second place for the wording to drift. The
    skill beside this had a third copy, written as a template for a model to
    fill in, and that one was measured being filled in from imagination.
    `--one-line` is the one implementation all of them now read.
    """
    where, entry = str(page.parent), page.name
    short = f"{page.parent.name}/{entry}" if page.parent.name else entry
    try:
        done = subprocess.run(
            ["assay", where, "-e", entry, "--if-page", "--one-line"],
            capture_output=True, text=True, timeout=PATIENCE)
    except FileNotFoundError:
        return (f"assay: could not check {short} because assay is not on "
                f"PATH, so nothing was verified.")
    except subprocess.TimeoutExpired:
        return (f"assay: gave up checking {short} after {PATIENCE}s, so "
                f"nothing was verified.")
    except Exception as slipped:
        return (f"assay: could not check {short} ({slipped}), so nothing "
                f"was verified.")

    # Exit 2 is a refusal and `--if-page` makes it silent: not a page this can
    # check, and the one case with genuinely nothing to report.
    return "" if done.returncode == 2 else done.stdout.strip()


def main() -> int:
    try:
        said = json.load(sys.stdin)
    except Exception:
        return 0

    # The harness's own loop guard, and it is free. Claude Code sets this on
    # the Stop that follows a Stop hook holding the turn open, which is
    # exactly the moment this must not speak again. Not every harness fills
    # it in, so it is one of two guards rather than the only one.
    if said.get("stop_hook_active"):
        return 0

    root = Path(said.get("cwd") or ".").resolve()
    clock = pages.clock(said.get("session_id", ""),
                        said.get("scratchpad_dir", ""), root)
    since = pages.last_run(clock)
    # Moved before the checking rather than after, so the step this forces is
    # measured from now and cannot re-report what it has just reported.
    remembered = pages.mark_run(clock)

    try:
        touched = pages.changed(root, since)
    except Exception:
        return 0
    if not touched:
        return 0

    lines = [line for page in touched if (line := summarise(page))]
    if not lines:
        return 0

    print(TELL, file=sys.stderr)
    print("", file=sys.stderr)
    print("\n".join(lines), file=sys.stderr)
    # **Holding the turn open is only safe while this can remember doing
    # it.** Exit 2 is what puts the line in front of the model, and it is
    # also what brings the next `Stop` round; with nowhere to record that
    # the check has run, the page still reads as changed and it says the
    # same thing again, forever. Unheard once is recoverable. A loop is not.
    return 2 if remembered else 0


if __name__ == "__main__":
    raise SystemExit(main())
