"""The `assay` command line."""

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


#: Checks for chromium in a subprocess. A second playwright instance in the
#: same process leaves the first one's tasks pending, and Python then prints
#: `Task was destroyed but it is pending!` and a `TargetClosedError` at exit,
#: after the results.
_PROBE = ("from playwright.sync_api import sync_playwright as s\n"
          "import pathlib, sys\n"
          "with s() as p:\n"
          "    sys.exit(0 if pathlib.Path(p.chromium.executable_path).exists()"
          " else 1)\n")


def ensure_browser() -> bool:
    """Download chromium on first use, so installing assay is one command.

    The check asks playwright for the browser's path instead of guessing its
    cache folder, because playwright has moved that folder before.
    """
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("assay: playwright isn't installed. Run pip install assay-ui "
              "to install it.", file=sys.stderr)
        return False

    here = subprocess.run([sys.executable, "-c", _PROBE],
                          capture_output=True, text=True)
    if here.returncode == 0:
        return True

    print("assay: Chromium isn't installed yet, so assay is downloading it. "
          "This only happens once.", file=sys.stderr)
    done = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        stdout=sys.stderr, stderr=sys.stderr)
    return done.returncode == 0


#: A script tag that loads an unbuilt source module. Bundlers like Vite and
#: Parcel keep a root `index.html` that points at source the browser can't
#: run, and write the built copy somewhere else.
_SOURCE_ENTRY = re.compile(
    r"""<script[^>]+src\s*=\s*['"](/?(?:src|app)/[^'"]+\.(?:jsx|tsx|ts|vue|svelte))['"]""",
    re.I)

#: Common build output folders, in the order to suggest them.
_BUILT = ("dist", "build", "out", ".output/public", "public")


def unbuilt(root: Path, entry: str) -> str:
    """Why this folder can't be checked as it is, or an empty string if it can.

    assay never runs a project's build. A served page runs inside the
    browser, in Chromium's sandbox wherever the system allows one, but
    `npm install` runs any `postinstall` script in the dependency tree with
    the user's privileges, and assay is for checking code nobody has read. A
    flag to allow builds wouldn't help, because people would add it once and
    stop thinking about it. Instead assay prints the build command, and the
    user runs it in their own shell and points assay at the output.
    """
    page = root / entry
    if page.is_file():
        found = _SOURCE_ENTRY.search(page.read_text(errors="replace")[:8000])
        if not found:
            return ""
        # Only the extension matters. A browser can't run JSX or TypeScript
        # whether or not the file exists.
        names = found.group(1)
        built = next((d for d in _BUILT if (root / d / "index.html").is_file()),
                     None)
        if built:
            return (f"{entry} loads {names}, which a browser can't run, but "
                    f"{built}/index.html is built.\n"
                    f"  Point assay at it:  assay {root}/{built}")
        return (f"{entry} loads {names}, which a browser can't run "
                f"without a build step.\n" + _build_it(root))

    if (root / "package.json").is_file():
        built = next((d for d in _BUILT if (root / d / "index.html").is_file()),
                     None)
        if built:
            return (f"there's no {entry} here, but {built}/index.html is "
                    f"built.\n"
                    f"  Point assay at it:  assay {root}/{built}")
        return (f"there's no {entry} here, but there's a package.json, so "
                f"the page probably comes from a build step.\n"
                + _build_it(root))
    return f"{root / entry} doesn't exist"


def _build_it(root: Path) -> str:
    """What to run, and why assay won't run it.

    Both messages in `unbuilt` that ask for a build use this text, so they
    can't drift apart.
    """
    return (f"  Build it in your own shell, then check the output:\n"
            f"    npm install && npm run build && assay {root}/dist\n"
            f"  assay won't run the build itself, because installing "
            f"dependencies runs their setup scripts, and assay is for "
            f"checking code nobody has read yet.")


#: Printed on stderr when Chromium's sandbox couldn't start. `run.Browser`
#: explains when that happens.
SANDBOX_OFF = ("assay: Chromium's sandbox couldn't start on this system, so "
               "the page ran without it.")


def _where(root: Path, entry: str) -> str:
    """The page as `folder/entry`, the way the one-line output names it."""
    # Resolve so `assay .` still gets a folder name, which tells apart two
    # pages that are both called `index.html`.
    folder = root.resolve().name
    return f"{folder}/{entry}" if folder else entry


def _flat(text: object) -> str:
    """Text from the page as a single line of printable characters.

    Labels and error messages come from the page, and an agent repeats the
    one-line output verbatim. A newline in one would let the page add a line
    of its own to the report, such as a false "nothing flagged".
    """
    return "".join(ch for ch in " ".join(str(text).split())
                   if ch.isprintable())


def one_line(run: object, root: Path, entry: str) -> str:
    """The whole run as one sentence, for a hook or skill to repeat verbatim.

    assay builds the sentence from the results so the agent never composes
    it. An agent filling in a template from worked examples can copy an
    example's details, including a false claim that the check didn't run. The
    hook and the skill print the same line, so they always agree.
    """
    from assay.qa import FAILED, PASSED

    results = getattr(run, "results", {})
    plan = getattr(run, "plan", [])
    where = _where(root, entry)
    bad = [r for r in results.values() if r.outcome == FAILED]
    # Count only the cases that ran and say how many didn't, so a page isn't
    # reported clean on the strength of checks that never happened.
    ran = sum(1 for c in plan
              if c.id in results and results[c.id].outcome in (PASSED, FAILED))
    missed = (f", {len(plan) - ran} couldn't be carried out"
              if ran < len(plan) else "")
    checks = "1 check" if len(plan) == 1 else f"{len(plan)} checks"
    head = f"assay: checked {where}, {checks}{missed}"
    if not bad:
        return f"{head}, nothing flagged."
    out = [f"{head}, {len(bad)} flagged:"]
    # This output has no case ids, so a repeat names the first finding by
    # its description.
    words = {r.case.id: _flat(r.case.what) for r in results.values()}
    for r in bad:
        notes = getattr(r, "links", [])
        same = [one for one in notes if one.kind == "same"]
        what = _flat(r.case.what)
        if same:
            out.append(f"  - {what} (same finding as "
                       f"{words.get(same[0].to, same[0].to)})")
            continue
        said = f"  - {what}: {_flat(r.detail)}" if r.detail \
            else f"  - {what}"
        for one in notes:
            if one.kind == "load":
                said += " (the page threw an error while loading, before " \
                        "anything was pressed)"
        out.append(said)
    return "\n".join(out)


def as_json(run: object, entry: str = "") -> str:
    """The whole run as JSON, for other tools.

    Console errors and failed requests are included but never fail a case,
    because a page can log an error or miss an icon and still work. They're
    often the first thing worth reading when a case did fail.
    """
    from assay.qa import PASSED

    results = getattr(run, "results", {})
    return json.dumps({
        "version": __version__,
        "entry": entry,
        "planned": len(getattr(run, "plan", [])),
        "passed": sum(1 for r in results.values() if r.outcome == PASSED),
        "failed": sum(1 for r in results.values() if r.failed),
        "works": getattr(run, "works", False),
        "sandboxed": getattr(run, "sandboxed", True),
        "surface": [
            {"kind": c.kind, "selector": c.selector, "label": c.label,
             "enabled": c.enabled}
            for c in getattr(run, "surface", None).controls
        ] if getattr(run, "surface", None) else [],
        "cases": [
            {"id": r.case.id, "what": r.case.what, "outcome": r.outcome,
             "detail": r.detail, "measured": r.evidence,
             "acts": r.case.acts, "rules": list(getattr(r, "rules", [])),
             "key": r.key if r.failed else "",
             "links": [{"kind": one.kind, "to": one.to, "why": one.why}
                       for one in getattr(r, "links", [])]}
            for r in results.values()
        ],
        "links": [{"from": r.case.id, "kind": one.kind, "to": one.to,
                   "why": one.why}
                  for r in results.values()
                  for one in getattr(r, "links", [])],
        "console_errors": list(getattr(run, "console_errors", [])),
        "failed_requests": list(getattr(run, "failed_requests", [])),
    }, indent=2)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Check one folder and print the result.

    Returns 0 when nothing failed, 1 when a case failed, and 2 when the page
    couldn't be checked. With `--if-page` that last case returns 0.
    """
    ap = argparse.ArgumentParser(
        prog="assay",
        description="An agent-native QA CLI for web pages. "
                    "Deterministic, no tests to write, no LLM.")
    ap.add_argument("folder",
                    help="the folder holding the page, or the page itself")
    ap.add_argument("-e", "--entry", default="index.html",
                    help="the page to open (default: index.html)")
    ap.add_argument("--report", metavar="FILE",
                    help="write an HTML report, with a screenshot per case")
    ap.add_argument("--json", action="store_true",
                    help="print the whole run as JSON instead")
    ap.add_argument("--one-line", action="store_true",
                    help="print a short summary of what was checked and what "
                         "was flagged, for an agent to quote in its reply")
    ap.add_argument("--if-page", action="store_true",
                    help="print nothing and exit 0 unless this is a page "
                         "assay can check, for hooks that run after every "
                         "edit")
    ap.add_argument("--surface", action="store_true",
                    help="print the controls the page offers, without "
                         "running any checks")
    ap.add_argument("--version", action="version",
                    version=f"assay {__version__}")
    args = ap.parse_args(argv)

    root, entry = aimed(args.folder, args.entry)
    # `--if-page` is for hooks that run after every edit. Most edits aren't
    # to a checkable page, and for those assay exits quietly instead of
    # printing an error into the agent's conversation. The decision lives
    # here so every harness's hook can just run assay and print its output.
    why = unbuilt(root, entry)
    if why:
        if args.if_page:
            return 0
        print(f"assay: {why}", file=sys.stderr)
        return 2
    if not ensure_browser():
        # The error is already on stderr. With `--if-page` the exit code
        # stays 0, so a hook doesn't fail the agent's turn over it, and the
        # reason also goes to stdout, because a hook passes on only stdout
        # and a page that wasn't checked mustn't look like silence.
        if args.if_page:
            print(f"assay: couldn't check {_where(root, entry)} because "
                  f"Chromium isn't installed and assay couldn't install it, "
                  f"so nothing was verified.")
            return 0
        return 2

    from assay import check, look, tint

    if args.surface:
        opened = look(root, entry)
        print(opened.surface.render())
        if not opened.sandboxed:
            print(SANDBOX_OFF, file=sys.stderr)
        return 0

    shots = None
    if args.report:
        # Name the screenshot folder after the report, so two reports in one
        # folder don't overwrite each other's screenshots.
        page = Path(args.report).expanduser()
        shots = page.with_name(f"{page.stem}-shots")

    run = check(root, entry, shots=shots)
    if not run.sandboxed:
        print(SANDBOX_OFF, file=sys.stderr)

    if args.json:
        print(as_json(run, entry))
    elif args.one_line:
        print(one_line(run, root, entry))
    else:
        print(run.render(colour=tint.enabled()))

    if args.report:
        from assay import report

        where = report.write(run, args.report, folder=root.name,
                             shots_dir=shots.name)
        print(f"\nreport written to {where}", file=sys.stderr)

    return 0 if run.works else 1


if __name__ == "__main__":
    raise SystemExit(main())
