"""Score assay against working programs and copies of them with planted bugs.

The generated benchmark only covers the bugs its programs happened to have.
This set starts from programs that work and plants bugs in a copy of each, so
assay is measured against a known list of bugs.

One harness and model wrote the programs, and a different harness and model
planted the bugs. Neither was told assay exists. `inject-prompt.txt` is the
injector's whole instruction, and it names no checker, rule or tool.

The scorer reports two numbers. Against `broken/`, it counts the planted bugs
assay found. Against `clean/`, it counts the working programs assay flagged
anyway. A tool that flagged everything would find every planted bug, so the
second number shows whether the first one means anything.

    python bench/planted/score.py                            # this set
    python bench/planted/score.py path/to/set --marker name   # another set
    python bench/planted/score.py --limit 2                  # writes nothing
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE.parent))

import linkkey  # noqa: E402
from machine import machine, plural, timing  # noqa: E402

#: The sentence for a set's block in the front-page README, with the counts
#: filled in from the run.
RESULTS = ("assay found {caught} of the {planted} planted bugs and flagged "
           "{noisy} of the {clean} original pages. "
           "[Every bug and result](https://github.com/awss1i/assay/blob/main/bench/planted/README.md).")

#: The title and description each known set gets on its own README.
ABOUT = {
    "planted": {
        "title": "The planted-bug set",
        "built": ("One harness and model wrote the programs from "
                  "[`objectives.txt`](objectives.txt). A **different** "
                  "harness and model put the bugs in, from the instruction "
                  "in [`inject-prompt.txt`](inject-prompt.txt), which names "
                  "no checker, no rule and no tool. Neither step was told "
                  "assay exists. `generate.sh` and `inject.sh` are the two "
                  "steps. assay's rules were developed with this set in "
                  "view, so its score is in-sample."),
    },
}


@dataclass
class Finding:
    """One flag, as the hand verdict names it."""

    key: str
    note: str = ""


@dataclass
class Planted:
    """One planted bug, and the findings the verdict says show it."""

    number: int
    found: List[Finding] = field(default_factory=list)
    note: str = ""

    @property
    def caught(self) -> bool:
        return bool(self.found)


@dataclass
class Program:
    """One program in the set, from either the broken or the clean copy."""

    name: str
    checks: int = 0
    seconds: float = 0.0
    #: Every failing case in this run, as `key -> case id`.
    failing: Dict[str, str] = field(default_factory=dict)
    bugs: List[Planted] = field(default_factory=list)
    #: Flags a person judged to be something other than a planted bug.
    other: List[Finding] = field(default_factory=list)
    error: str = ""
    #: True when the program has no verdict yet, which stops the scorer
    #: writing anything.
    unread: bool = False
    #: The links the run drew between its findings. See `bench/linkkey.py`.
    links: set = field(default_factory=set)

    @property
    def flagged(self) -> int:
        return len(self.failing)

    @property
    def caught(self) -> int:
        return sum(1 for b in self.bugs if b.caught)

    @property
    def stale(self) -> List[str]:
        """Keys the verdict names that didn't fail in this run.

        The verdict was judged against a run where these findings failed, so
        any stale key stops the scorer writing instead of being counted.
        """
        named = [f.key for b in self.bugs for f in b.found] \
            + [f.key for f in self.other]
        return [k for k in named if k not in self.failing]

    @property
    def unjudged(self) -> List[str]:
        """Failing keys the verdict doesn't mention.

        Whether a flag shows a planted bug or something else takes judgement,
        so the scorer writes nothing while any flag on a broken program is
        unjudged.
        """
        named = {f.key for b in self.bugs for f in b.found} \
            | {f.key for f in self.other}
        return [k for k in self.failing if k not in named]


#: A verdict line. An `other` line has no bug number because its flag isn't a
#: planted bug.
_LINE = re.compile(r"^(?:(?P<n>\d+)\s+(?P<said>found|missed)|(?P<other>other))"
                   r"\s*(?P<rest>.*)$")


def planted_count(where: Path) -> int:
    """How many bugs the injector says it planted, from its own `bugs.md`."""
    path = where / "bugs.md"
    if not path.is_file():
        return 0
    return len(re.findall(r"(?m)^\s*\d+\.", path.read_text(encoding="utf-8")))


def read_verdict(where: Path) -> tuple:
    """Read one program's `verdict.txt` as its planted bugs and other flags.

    A planted bug counts as found when at least one failing case shows it.
    assay reports what it did and what it measured, and only a person can
    decide whether that measurement is this bug. So the file is written by
    hand, and any line this can't parse raises ValueError.
    """
    path = where / "verdict.txt"
    if not path.is_file():
        return [], []
    bugs: Dict[int, Planted] = {}
    other: List[Finding] = []
    for at, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        got = _LINE.match(line)
        if not got:
            raise ValueError(f"{path}:{at}: can't read {line!r}")
        rest = got["rest"].strip()
        if got["other"] or got["said"] == "found":
            key, bar, note = rest.partition(" | ")
            if not bar or "@" not in key:
                raise ValueError(f"{path}:{at}: expected '<key> | <note>'")
            one = Finding(key.strip(), note.strip())
            if got["other"]:
                other.append(one)
            else:
                bug = bugs.setdefault(int(got["n"]), Planted(int(got["n"])))
                bug.found.append(one)
        else:
            number = int(got["n"])
            if number in bugs:
                raise ValueError(f"{path}:{at}: bug {number} is both found "
                                 f"and missed")
            bugs[number] = Planted(number, note=rest)
    return [bugs[n] for n in sorted(bugs)], other


def run(folder: Path, verdicts: bool) -> Program:
    """Check one program and record what assay said about it."""
    from assay import check

    got = Program(name=folder.name)
    began = time.time()
    try:
        done = check(folder, "index.html")
    except Exception as exc:
        got.error = f"assay raised: {str(exc)[:120]}"
        return got
    got.seconds = time.time() - began
    got.checks = len(done.plan)
    got.failing = {r.key: r.case.id for r in done.failing}
    got.links = linkkey.drawn(list(done.results.values()))
    if verdicts:
        got.bugs, got.other = read_verdict(folder)
        numbers = [b.number for b in got.bugs]
        expected = planted_count(folder)
        # A program with no verdict yet is new to the set, so its flags print
        # as unjudged and nothing is written. A verdict that exists must cover
        # every planted bug.
        if not (folder / "verdict.txt").is_file():
            got.bugs = [Planted(n, note="no verdict yet")
                        for n in range(1, expected + 1)]
            got.unread = True
        elif numbers != list(range(1, expected + 1)):
            raise ValueError(f"{folder}/verdict.txt covers bugs {numbers}, "
                             f"and bugs.md plants {expected}")
    return got


def read_excluded(root: Path) -> Dict[str, str]:
    """Read `EXCLUDED`, the programs left out of scoring and why.

    Each line is `<kind>/<name> <reason>`. A clean program found broken before
    the set was first scored is left out, because a flag on it wouldn't be a
    false alarm. The reason is published with the numbers.
    """
    path = root / "EXCLUDED"
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, _, why = line.partition(" ")
            out[name] = why.strip()
    return out


def sweep(root: Path, verdicts: bool, limit: int,
          excluded: Optional[Dict[str, str]] = None) -> List[Program]:
    """Check every program under `root` in order, skipping excluded ones."""
    out = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        if limit and len(out) >= limit:
            break
        if not (folder / "index.html").is_file():
            continue
        if f"{root.name}/{folder.name}" in (excluded or {}):
            print(f"  {folder.name:<16} excluded before scoring")
            continue
        got = run(folder, verdicts)
        if got.error:
            print(f"  {got.name:<16} ERROR {got.error}")
        else:
            mark = (f"{got.caught}/{len(got.bugs)} planted" if got.bugs
                    else f"{got.flagged} flagged")
            print(f"  {got.name:<16} {got.checks:>3} checks  {mark:<14} "
                  f"{got.seconds:>6.1f}s")
        for key in got.stale:
            print(f"    !! the verdict names {key!r}, which didn't fail")
        for key in got.unjudged:
            print(f"    ?? {got.failing[key]} {key!r} failed and no verdict "
                  f"line says what it is")
        out.append(got)
    return out


def write_readme(root: Path, marker: str, broken: List[Program],
                 clean: List[Program], measured_on: str,
                 marks: "linkkey.Marks",
                 excluded: Optional[Dict[str, str]] = None) -> None:
    """Rewrite the set's `README.md` from this run."""
    about_it = about(marker)
    planted = sum(len(p.bugs) for p in broken)
    caught = sum(p.caught for p in broken)
    noisy = [p for p in clean if p.flagged]
    other = [(p, f) for p in broken for f in p.other]
    seconds = [p.seconds for p in broken + clean]

    # The header is HTML so it can be centred, and markdown inside an HTML
    # block isn't rendered, so its code is HTML too.
    out = [f'<h1 align="center">{about_it["title"]}</h1>',
           "",
           "---",
           "",
           '<p align="center"><i><code>planted/score.py</code> writes this '
           "page, and the checks, flags and times come from running it. "
           "Which planted bug each flag shows is judged by hand in each "
           "<code>verdict.txt</code>.</i></p>",
           "",
           f'<p align="center">{len(broken)} programs with bugs a separate '
           f"agent planted on purpose ({planted} in all, as listed in each "
           f"<code>bugs.md</code>), and {len(clean)} working originals.</p>",
           "",
           "---",
           "",
           "## Contents",
           "",
           "- [What assay Found](#what-assay-found)",
           "- [Every Planted Bug](#every-planted-bug)",
           "- [How the Set Was Built](#how-the-set-was-built)",
           "",
           "---",
           "",
           "## What assay Found",
           "",
           f"- **{caught} of the {planted} planted bugs found.**",
           f"- **{len(noisy)} of the {len(clean)} working originals "
           f"flagged**"
           + (f": {', '.join(p.name for p in noisy)}" if noisy else "."),
           f"- **{plural(len(other), 'flag')} on broken programs that aren't a "
           f"planted bug.**",
           f"- **Grouped findings:** {marks.sentence()}.",
           ""]
    if seconds:
        out += [f"Per program, {timing(seconds)}. assay ran on {measured_on}.",
                ""]
    if other:
        out += ["| program | flag | what it is |", "|---|---|---|"]
        out += [f"| {p.name} | `{f.key}` | {f.note} |" for p, f in other]
        out.append("")

    if excluded:
        out += ["Left out of the score before it was run, and why:", ""]
        out += [f"- `{name}`: {why}" for name, why in excluded.items()]
        out.append("")

    out += ["---", "", "## Every Planted Bug", ""]
    for p in broken:
        out += [f"### {p.name}", "",
                f"{p.checks} checks, {p.flagged} flagged, {p.caught} of "
                f"{len(p.bugs)} planted bugs found.", "",
                "| bug | assay | which finding |", "|---|---|---|"]
        for b in p.bugs:
            if b.caught:
                said = ". ".join(
                    f"{p.failing.get(f.key, '?')} `{f.key}`: {f.note}"
                    for f in b.found)
                out.append(f"| {b.number} | found | {said} |")
            else:
                out.append(f"| {b.number} | missed | {b.note or '-'} |")
        out.append("")

    out += ["---", "", "## How the Set Was Built", "",
            about_it["built"],
            "",
            "Each broken program has a `bugs.md` from the model that added "
            "the bugs, and a `verdict.txt` recording, for each bug, whether "
            "assay caught it and with which finding. Findings are named by "
            "the rule and the check, not by case number, so verdicts stay "
            "correct when checks are added or reordered.",
            "",
            "Deciding whether a failure is a particular planted bug is a "
            "judgement, so it's made by hand and written down, not matched "
            "by a script.",
            ""]
    (root / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def about(marker: str) -> Dict[str, str]:
    """The title and description for a set, with generic ones for a set not in
    `ABOUT`."""
    return ABOUT.get(marker, {
        "title": f"The {marker} set",
        "built": ("Built the same way as the planted set, with "
                  "`bench/planted/generate.sh` and `bench/planted/inject.sh`."),
    })


def _write_headline(readme: Path, marker: str, **counts: object) -> None:
    """Fill the marked block in the front-page README with this run."""
    if not readme.is_file():
        return
    text = readme.read_text(encoding="utf-8")
    opened, closed = f"<!-- {marker} -->", f"<!-- /{marker} -->"
    if opened not in text or closed not in text:
        return
    head, _, rest = text.partition(opened)
    _, _, tail = rest.partition(closed)
    readme.write_text(head + opened + "\n\n"
                      + RESULTS.format(**counts)
                      + "\n\n" + closed + tail, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path, nargs="?", default=HERE,
                    help="the set, holding broken/ and clean/ "
                         "(default: the one beside this script)")
    ap.add_argument("--marker", default="planted",
                    help="the name of the set, and the front-page block its "
                         "headline goes in, if the README has one")
    ap.add_argument("--limit", type=int, default=0,
                    help="only the first N of each, for a quick check. It "
                         "writes nothing")
    args = ap.parse_args(argv)
    root = args.root.resolve()

    began = time.time()
    try:
        excluded = read_excluded(root)
        print("broken:")
        broken = sweep(root / "broken", True, args.limit, excluded)
        print("clean:")
        clean = sweep(root / "clean", False, args.limit, excluded)
    except ValueError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    planted = sum(len(p.bugs) for p in broken)
    caught = sum(p.caught for p in broken)
    noisy = sum(1 for p in clean if p.flagged)
    print(f"\nassay found {caught} of {planted} planted bugs, "
          f"{noisy} of {len(clean)} clean programs flagged, "
          f"{time.time() - began:.0f}s in all")

    marks = linkkey.Marks()
    # A set's own links.txt adds to the shared key.
    key = {**linkkey.read(), **linkkey.read(root / "links.txt")}
    drawn_by = {}
    for kind, programs in (("broken", broken), ("clean", clean)):
        for p in programs:
            drawn_by[f"{args.marker}/{kind}/{p.name}"] = p.links
            marks.mark(f"{args.marker}/{kind}/{p.name}", p.links, key)
    print(f"links: {marks.sentence()}")
    for program, one in marks.wrong:
        print(f"  !! wrong link on {program}: {one}", file=sys.stderr)
    for program in marks.unjudged:
        print(f"  ?? {program} drew links nobody has judged: "
              f"{sorted(drawn_by[program])}", file=sys.stderr)

    errors = [p for p in broken + clean if p.error]
    stale = sum(len(p.stale) for p in broken)
    unjudged = sum(len(p.unjudged) for p in broken) + sum(
        1 for p in broken if p.unread)
    if errors or stale or unjudged or marks.wrong or marks.unjudged:
        print("Nothing is written until each of these is zero.\n"
              f"  programs that couldn't be checked: {len(errors)}\n"
              f"  verdict lines naming a finding that didn't fail: {stale}\n"
              f"  flags with no verdict: {unjudged}\n"
              f"  programs whose links are wrong: {len(marks.wrong)}\n"
              f"  programs whose links aren't judged: {len(marks.unjudged)}",
              file=sys.stderr)
        return 1

    if args.limit:
        print("quick check, nothing written")
    else:
        write_readme(root, args.marker, broken, clean, machine(), marks,
                     excluded)
        _write_headline(REPO / "README.md", args.marker, caught=caught,
                        planted=planted, noisy=noisy, clean=len(clean),
                        grouping=marks.grouping())
        print(f"written: {root / 'README.md'} and the front-page headline")
    return 1 if noisy else 0


if __name__ == "__main__":
    raise SystemExit(main())
