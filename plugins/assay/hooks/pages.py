"""Find the pages a turn changed by comparing file modification times.

Every way of editing a file updates its mtime, whether it's the `Edit` tool,
`sed -i` in a shell, `cat >` or a script the model wrote. Watching tool calls
instead would miss edits made through the shell.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

#: Files that can change what a page does. Editing `app.js` changes the page
#: without touching any HTML.
WEB = {".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".svg",
       ".jsx", ".ts", ".tsx", ".vue", ".json"}

#: Directories the scan skips, along with any hidden directory. Dependency
#: folders like `node_modules` can hold thousands of pages nobody edited.
SKIP = {"node_modules", ".git", ".venv", "venv", "__pycache__", ".next",
        ".cache", ".pytest_cache", "vendor", ".tox"}

#: How many directory levels below the working directory to scan. Pages and
#: build output like `dist/` sit near the top, and a page much deeper usually
#: belongs to something else.
DEEP = 4

#: Seconds to look back on a session's first run, when there's no last-run
#: time. Long enough to cover the turn that just ended, and short enough to
#: skip pages edited in an earlier session.
FIRST_LOOK = 30 * 60

#: The most pages checked per turn. Each check starts a browser, so when a
#: turn changes a whole site only its most recently changed pages are checked.
MOST = 3


def changed(root: Path, since: float) -> list[Path]:
    """Return up to `MOST` pages changed since `since`, newest first.

    A directory counts as changed when any web file in it changed, and the
    page checked for it is its most recently modified `.html` or `.htm` file.
    `index.html` wins a tie, because a folder with several pages is usually
    entered through it. Pages aren't always called `index.html`. A one-file
    app is often `todo.html` or `game.html`.
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
    """Return the file where this session records when the check last ran.

    The file has to survive between hook runs, and the temp directory doesn't
    always. The DeepSeek Harness runs hooks with a private `/tmp` that's gone
    by the next run, so a time kept there is lost and the hook reports the
    same pages on every `Stop`.

    The order of preference is a scratch folder the harness passes in, then
    the git directory of the repository the working directory is in (nothing
    there shows in `git status`), then a single `.assay-last-run` in the
    working directory. The temp directory is used only when there's no
    working directory.
    """
    tag = hashlib.sha1(session.encode()).hexdigest()[:12]
    if scratch and Path(scratch).is_dir():
        return Path(scratch) / f"assay-last-run-{tag}"
    if root is not None:
        git = git_dir(root)
        if git is not None:
            return git / f"assay-last-run-{tag}"
        # One file per folder instead of one per session, so the user's
        # project doesn't fill up with files. Two sessions in one folder share
        # it, which at worst repeats a report.
        return root / ".assay-last-run"
    return Path(tempfile.gettempdir()) / f"assay-last-run-{tag}"


def git_dir(root: Path) -> Optional[Path]:
    """The git directory of the repository `root` is in, or None.

    The working directory can be any folder inside the repository. `.git` is
    a folder in an ordinary clone, and in a worktree or submodule it's a file
    whose `gitdir:` line names the real folder.
    """
    for here in (root, *root.parents):
        dot = here / ".git"
        if dot.is_dir():
            return dot
        if dot.is_file():
            try:
                said = dot.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            if not said.startswith("gitdir:"):
                return None
            target = here / said[len("gitdir:"):].strip()
            return target if target.is_dir() else None
    return None


def last_run(path: Path) -> float:
    """When the check last ran, or far enough back to catch this turn."""
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return time.time() - FIRST_LOOK


def mark_run(path: Path) -> bool:
    """Record that the check just ran. Returns False if the write failed.

    The caller only holds the turn open when this returns True, so a failed
    write can't cause a reporting loop.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(time.time()), encoding="utf-8")
        return True
    except OSError:
        return False
