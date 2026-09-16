"""`assay ./my-app`, the command line."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

from assay import __version__
from assay.run import aimed


#: Asked in a subprocess, and that is the whole point of it. Starting a second
#: playwright inside one process leaves its first connection's tasks pending,
#: and python says so at exit: several lines of `Task was destroyed but it is
#: pending!` and a `TargetClosedError`, printed *after* the results, which
#: reads to anybody running this as a crash rather than a tidy-up. Verified by
#: bisection: one instance is silent, two are not.
_PROBE = ("from playwright.sync_api import sync_playwright as s\n"
          "import pathlib, sys\n"
          "with s() as p:\n"
          "    sys.exit(0 if pathlib.Path(p.chromium.executable_path).exists()"
          " else 1)\n")


def ensure_browser() -> bool:
    """Fetch chromium the first time, so installing assay is one command.

    Two steps is where a tool loses people, and `playwright install` is the
    step nobody remembers. Asked of playwright itself rather than guessed at
    from a cache path, because where it keeps its browsers is its business and
    has changed before.
    """
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("assay: playwright is not installed. Run pip install assay-ui",
              file=sys.stderr)
        return False

    here = subprocess.run([sys.executable, "-c", _PROBE],
                          capture_output=True, text=True)
    if here.returncode == 0:
        return True

    print("assay: no browser yet, fetching chromium. One moment...",
          file=sys.stderr)
    done = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        stdout=sys.stderr, stderr=sys.stderr)
    return done.returncode == 0


#: What a bundler's entry page points at before anything has been built.
#: Vite, Parcel and the rest write a root `index.html` that names a source
#: module the browser cannot load, and the built copy goes somewhere else.
_SOURCE_ENTRY = re.compile(
    r"""<script[^>]+src\s*=\s*['"](/?(?:src|app)/[^'"]+\.(?:jsx|tsx|ts|vue|svelte))['"]""",
    re.I)

#: Where a build usually lands, in the order worth suggesting.
_BUILT = ("dist", "build", "out", ".output/public", "public")


def unbuilt(root: Path, entry: str) -> str:
    """Why this folder cannot be opened as it stands, or empty if it can.

    **assay does not run your build, and that is a decision rather than a gap
    left to fill in later.** Serving a folder is safe because the browser is
    the sandbox: nothing in the page can reach the machine it is measured on.
    `npm install` has no such property, because it runs whatever `postinstall` the
    dependency tree asks for, with the privileges of whoever typed the
    command, and the code under test here is by definition code nobody has
    read. A tool whose whole audience is people checking programs they did
    not write must not be the thing that executes them.

    A flag would not fix it either. `--allow-build` would be passed by
    everybody, once, in the shell history, and never thought about again.

    So the answer is to say what to run. The user builds in their own shell,
    where they were already deciding what to trust, and points assay at the
    output. One extra command, and the boundary stays where it can be seen.
    """
    page = root / entry
    if page.is_file():
        found = _SOURCE_ENTRY.search(page.read_text(errors="replace")[:8000])
        if not found:
            return ""
        # Whether the file is *there* decides nothing: a browser cannot run
        # JSX or TypeScript either way, and it being present is exactly what
        # an unbuilt source tree looks like. The extension is the whole test.
        names = found.group(1)
        built = next((d for d in _BUILT if (root / d / "index.html").is_file()),
                     None)
        if built:
            return (f"{entry} loads {names}, which a browser cannot run, but "
                    f"{built}/index.html is built.\n"
                    f"  Point assay at it:  assay {root}/{built}")
        return (f"{entry} loads {names}, which a browser cannot run. This is "
                f"a source tree, not a built one.\n" + _build_it(root))

    if (root / "package.json").is_file():
        built = next((d for d in _BUILT if (root / d / "index.html").is_file()),
                     None)
        if built:
            return (f"no {entry} here, but {built}/index.html is built.\n"
                    f"  Point assay at it:  assay {root}/{built}")
        return (f"no {entry} here, and package.json says this is a source "
                f"tree.\n" + _build_it(root))
    return f"{root / entry} does not exist"


def _build_it(root: Path) -> str:
    """What to run, and why assay will not run it.

    Said in both places a source tree is recognised, which is why it is one
    string: the same paragraph written twice is a paragraph that ends up
    saying two different things.
    """
    return (f"  Build it first, in your own shell, then check the output:\n"
            f"    npm install && npm run build && assay {root}/dist\n"
            f"  assay will not run that for you: installing dependencies "
            f"executes their setup scripts, and this is a tool for checking "
            f"code nobody has read.")


def one_line(run: object, root: Path, entry: str) -> str:
    """The whole run as the one sentence something else will repeat.

    **A filled-in example is an answer, and it gets copied.** The first
    version of this lived in a skill file as a sentence the model was asked
    to compose, with three worked examples above it. On a live harness run
    the model copied the one about assay not being on PATH, word for word,
    including a folder name from the example and a cause that was not true:
    assay *was* on PATH, and the page was checked. A check that did not
    happen must never read like one that passed, and a check that *did*
    happen must never be reported as one that could not.

    So the sentence is computed where the facts are and handed over whole.
    Nothing downstream has a template to fill in, which is what makes the
    copying impossible rather than discouraged, and the hook and the skill
    say the same thing because they are reading the same line.
    """
    from assay.qa import FAILED, PASSED

    results = getattr(run, "results", {})
    plan = getattr(run, "plan", [])
    # Resolved, because `assay .` has no name of its own and the folder is
    # exactly what tells two pages called `index.html` apart.
    folder = root.resolve().name
    where = f"{folder}/{entry}" if folder else entry
    bad = [r for r in results.values() if r.outcome == FAILED]
    # **A check that did not happen must never read like one that passed.**
    # A case can fail to be carried out at all, and counting only the
    # failures would report a page as clean on the strength of checks that
    # never ran. It is the same reason assay's own summary says how many of
    # the planned cases were carried out.
    ran = sum(1 for c in plan
              if c.id in results and results[c.id].outcome in (PASSED, FAILED))
    missed = (f", {len(plan) - ran} could not be carried out"
              if ran < len(plan) else "")
    head = f"assay: checked {where}, {len(plan)} checks{missed}"
    if not bad:
        return f"{head}, nothing flagged."
    out = [f"{head}, {len(bad)} flagged:"]
    out += [f"  - {r.case.what}: {r.detail}" if r.detail
            else f"  - {r.case.what}" for r in bad]
    return "\n".join(out)


def as_json(run: object) -> str:
    """The whole run, for something that is not a person."""
    from assay.qa import PASSED

    results = getattr(run, "results", {})
    return json.dumps({
        "planned": len(getattr(run, "plan", [])),
        "passed": sum(1 for r in results.values() if r.outcome == PASSED),
        "failed": sum(1 for r in results.values() if r.failed),
        "works": getattr(run, "works", False),
        "surface": [
            {"kind": c.kind, "selector": c.selector, "label": c.label,
             "enabled": c.enabled}
            for c in getattr(run, "surface", None).controls
        ] if getattr(run, "surface", None) else [],
        "cases": [
            {"id": r.case.id, "what": r.case.what, "outcome": r.outcome,
             "detail": r.detail, "measured": r.evidence,
             "acts": r.case.acts}
            for r in results.values()
        ],
    }, indent=2)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Check one folder and say what happened. Non-zero if anything failed."""
    ap = argparse.ArgumentParser(
        prog="assay",
        description="Find out if a generated web page actually works. "
                    "No tests written, no LLM.")
    ap.add_argument("folder",
                    help="the folder holding the program, or the page")
    ap.add_argument("-e", "--entry", default="index.html",
                    help="the page to open (default: index.html)")
    ap.add_argument("--report", metavar="FILE",
                    help="write an HTML report, with a screenshot per case")
    ap.add_argument("--json", action="store_true",
                    help="print the whole run as JSON instead")
    ap.add_argument("--one-line", action="store_true",
                    help="print one sentence saying what was checked and "
                         "what was flagged, for something that has to repeat "
                         "it")
    ap.add_argument("--if-page", action="store_true",
                    help="say nothing and exit 0 unless this is a page assay "
                         "can check; for hooks that fire on every edit")
    ap.add_argument("--surface", action="store_true",
                    help="only report what the program offers, and stop")
    ap.add_argument("--version", action="version",
                    version=f"assay {__version__}")
    args = ap.parse_args(argv)

    root, entry = aimed(args.folder, args.entry)
    # **`--if-page` is for the thing that calls assay without being asked.**
    # An editor hook fires on every write, and most writes are not a page:
    # a Rust file, a README, a component in a source tree. Told that each
    # time, a hook is a machine for generating noise, and the noise arrives
    # in somebody's conversation.
    #
    # The judgement belongs here rather than in the hook. `unbuilt` already
    # answers it, and it is the same answer in every harness, so a hook
    # anywhere can be three lines that run this and print what comes back.
    # A rule written once and tested against 225 programs beats the same
    # rule written four times in four shell scripts that nobody benchmarks.
    why = unbuilt(root, entry)
    if why:
        if args.if_page:
            return 0
        print(f"assay: {why}", file=sys.stderr)
        return 2
    if not ensure_browser():
        # A missing browser is worth saying out loud, and is never worth
        # failing a turn over: stderr carries it where somebody will see it
        # and the exit code keeps the caller out of it.
        return 0 if args.if_page else 2

    from assay import check, look, tint

    if args.surface:
        print(look(root, entry).surface.render())
        return 0

    shots = None
    if args.report:
        shots = Path(args.report).expanduser().parent / "shots"

    run = check(root, entry, shots=shots)

    if args.json:
        print(as_json(run))
    elif args.one_line:
        print(one_line(run, root, entry))
    else:
        print(run.render(colour=tint.enabled()))

    if args.report:
        from assay import report

        where = report.write(run, args.report, folder=root.name)
        print(f"\nreport: {where}", file=sys.stderr)

    return 0 if run.works else 1


if __name__ == "__main__":
    raise SystemExit(main())
