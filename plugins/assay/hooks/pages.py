"""Which pages a turn changed, found by looking at the disk.

**Not by watching tool calls.** The first version of this noted every `Write`
and `Edit`, which missed the first real thing anybody tried: a model asked to
add one comment ran `sed -i` through the shell, matched no edit tool, and the
check never fired. Parsing file paths out of arbitrary shell commands is a
losing game and the next way round it would have been a script the model wrote
thirty seconds earlier.

Every method of editing a file leaves the same evidence, so that is what is
read. `sed`, `Edit`, `cat >`, a generated script: all of them change an mtime.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

#: Files that can change what a page does. **Not just `.html`.** Editing
#: `app.js` changes the page and touches no HTML at all.
WEB = {".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".svg",
       ".jsx", ".ts", ".tsx", ".vue", ".json"}

#: Never worth walking into, and the first one is why a bounded scan is cheap
#: at all: a dependency tree holds thousands of pages nobody wrote.
SKIP = {"node_modules", ".git", ".venv", "venv", "__pycache__", ".next",
        ".cache", ".pytest_cache", "vendor", ".tox"}

#: How deep below the working directory to look. Built output sits at `dist/`
#: or `build/`, and a page five levels down belongs to something else.
DEEP = 4

#: How far back to look on the first run of a session, when there is no
#: previous run to measure from. Long enough to cover the turn that just
#: happened, short enough to ignore a page last touched yesterday.
FIRST_LOOK = 30 * 60

#: Checking is a browser each, so a turn that rewrites a whole site reports on
#: the few that changed most recently rather than sitting there for a minute.
MOST = 3


def changed(root: Path, since: float) -> list[Path]:
    """Pages that have changed since `since`, newest first.

    **A page is not called `index.html`.** Asked for a to-do list in one file,
    a model wrote `todo.html`, and a scan looking for that one name saw
    nothing at all. `app.html`, `demo.html`, `game.html` are all ordinary, and
    the name is the model's to choose.

    So a directory is interesting when any web file in it changed, and what
    gets checked is the page in that directory: the most recently written
    `.html`, or `index.html` when they are level, because that is the one a
    folder with several pages is usually entered through.

    Newest first, because past `MOST` the ones just written are the ones
    somebody is working on.
    """
    found: dict[Path, float] = {}
    for here, dirs, files in os.walk(root):
        spot = Path(here)
        if len(spot.relative_to(root).parts) >= DEEP:
            dirs[:] = []
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]

        pages, touched = [], 0.0
        for name in files:
            if Path(name).suffix.lower() not in WEB:
                continue
            try:
                when = (spot / name).stat().st_mtime
            except OSError:
                continue
            touched = max(touched, when)
            if name.lower().endswith((".html", ".htm")):
                # `index.html` wins a tie, hence the second key.
                pages.append((when, name.lower() == "index.html", name))
        if pages and touched > since:
            found[spot / max(pages)[2]] = touched
    return [p for p, _ in sorted(found.items(), key=lambda kv: -kv[1])][:MOST]


def clock(session: str, scratch: str = "",
          root: Optional[Path] = None) -> Path:
    """Where this session records when the check last ran.

    **The temp directory is the obvious place and it is the wrong one.** A
    harness may run a hook with a private `/tmp`, and the DeepSeek Harness
    does: the file is written, reads back inside the same process, and is
    gone by the next invocation. A store that lasts exactly as long as the
    process testing it is indistinguishable from one that works, so nothing
    reported a fault. What it bought was **eleven identical reports in three
    minutes**, each one holding the turn open, because a check that cannot
    remember looking looks again forever.

    So the order is about what survives rather than about tidiness. A
    scratch folder the harness passes in comes first. Otherwise the
    workspace, the one place every harness can write and nothing clears,
    because it is where the work is. Inside it `.git` is preferred, since
    git never shows what is in there and a repository is the common case; a
    folder that is not one gets a single dotfile in it.
    """
    tag = hashlib.sha1(session.encode()).hexdigest()[:12]
    if scratch and Path(scratch).is_dir():
        return Path(scratch) / f"assay-last-run-{tag}"
    if root is not None:
        if (root / ".git").is_dir():
            return root / ".git" / f"assay-last-run-{tag}"
        # One file per folder rather than one per session: two sessions
        # working in one folder is rare, and the worst it costs is a report
        # the other one already made. Accumulating a file per session in
        # somebody's project is worse than that every time.
        return root / ".assay-last-run"
    return Path(tempfile.gettempdir()) / f"assay-last-run-{tag}"


def last_run(path: Path) -> float:
    """When the check last ran, or far enough back to catch this turn."""
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return time.time() - FIRST_LOOK


def mark_run(path: Path) -> bool:
    """Record that the check has just run. False if it could not be.

    **The caller needs the answer, and for a while it was thrown away.** This
    swallowed its own failure, so a hook whose memory did not work behaved
    exactly like one whose memory did, and the only symptom was the loop.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(time.time()), encoding="utf-8")
        return True
    except OSError:
        return False
