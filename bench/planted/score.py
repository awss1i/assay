"""Score assay against a set of programs whose defects are known in advance.

The 225-program benchmark can only ever tell you about twenty defects,
because that is how many of those programs are broken. This set is built the
other way round: ten programs that work, and a copy of each with five bugs
put into it deliberately, so recall is measured against fifty defects instead
of twenty.

**Nothing about assay chose the defects.** The programs were written by one
harness and model, the bugs were put in by a different harness and model, and
neither was told assay exists. `inject-prompt.txt` is the whole instruction
the injector was given, and it names no checker, no rule and no tool.

Two numbers come out. Against `broken/`, how many of the fifty planted bugs
assay flagged. Against `clean/`, how many working programs it flagged anyway,
which is the number that decides whether the first one means anything.

    python bench/planted/score.py            # both, and rewrite README.md
    python bench/planted/score.py --limit 2  # the first two of each
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))


@dataclass
class Planted:
    """One deliberately introduced bug, and what assay made of it."""

    number: int
    found: bool
    case: str = ""
    note: str = ""


@dataclass
class Program:
    """One program from the set, in whichever copy is being scored."""

    name: str
    flagged: int = 0
    checks: int = 0
    cases: List[str] = field(default_factory=list)
    #: The ids of the cases that failed in this run.
    failing: List[str] = field(default_factory=list)
    bugs: List[Planted] = field(default_factory=list)

    @property
    def caught(self) -> int:
        return sum(1 for b in self.bugs if b.found)

    @property
    def stale(self) -> List[Planted]:
        """Bugs marked found by a case that did not fail in this run.

        A verdict names the case that showed the bug, and a plan can change
        under it. A case that no longer fails is a verdict about a run that
        is gone, so it is refused rather than counted.
        """
        return [b for b in self.bugs if b.found and b.case not in self.failing]


def read_verdict(where: Path) -> List[Planted]:
    """The hand verdict for one program, or nothing if it has none yet.

    A planted bug is *found* when at least one failing case is caused by it,
    which is a judgement nothing mechanical can make: assay reports an act and
    a measurement, and whether that measurement is this bug showing itself is
    exactly the thing a person has to decide. So the file is written by hand
    and this only reads it.
    """
    path = where / "verdict.txt"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        bits = line.split(None, 2)
        number, said = int(bits[0]), bits[1]
        rest = bits[2] if len(bits) > 2 else ""
        if said == "found":
            case, _, note = rest.partition(" ")
            out.append(Planted(number, True, case, note.strip()))
        else:
            out.append(Planted(number, False, note=rest.strip()))
    return out


def run(folder: Path, verdicts: bool) -> Program:
    """Check one program and record what assay said about it."""
    from assay import check
    from assay.qa import FAILED

    done = check(folder, "index.html")
    bad = [r for r in done.results.values() if r.outcome == FAILED]
    return Program(
        name=folder.name,
        flagged=len(bad),
        checks=len(done.plan),
        cases=[f"{r.case.id} {r.case.what}: {r.detail}" for r in bad],
        failing=[r.case.id for r in bad],
        bugs=read_verdict(folder) if verdicts else [])


def sweep(root: Path, verdicts: bool, limit: int) -> List[Program]:
    """Every program under `root`, in order."""
    out = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        if limit and len(out) >= limit:
            break
        if not (folder / "index.html").is_file():
            continue
        got = run(folder, verdicts)
        mark = (f"{got.caught}/{len(got.bugs)} planted" if got.bugs
                else f"{got.flagged} flagged")
        print(f"  {got.name:<16} {got.checks:>3} checks  {mark}")
        for bug in got.stale:
            print(f"    !! bug {bug.number} is marked found by {bug.case}, "
                  f"which did not fail in this run")
        out.append(got)
    return out


def write_readme(broken: List[Program], clean: List[Program]) -> None:
    """The record, rewritten from what just ran."""
    planted = sum(len(p.bugs) for p in broken)
    caught = sum(p.caught for p in broken)
    scored = [p for p in broken if p.bugs]
    noisy = [p for p in clean if p.flagged]

    out = ["# The planted-bug set",
           "",
           "*Generated by `planted/score.py`. The checks and flags come from "
           "running it. Which planted bug a flag shows is judged by hand in "
           "each `verdict.txt`, and the scorer refuses a verdict whose case "
           "did not fail.*",
           "",
           "Ten programs that work, and a copy of each with five bugs put "
           "into it deliberately. The 225-program benchmark holds twenty "
           "defects in total, so it can only say so much about what assay "
           "misses. This set exists to say more.",
           "",
           "## Contents",
           "",
           "- [What It Found](#what-it-found)",
           "- [Every Planted Bug](#every-planted-bug)",
           "- [How the Set Was Built](#how-the-set-was-built)",
           ""]

    out += ["## What It Found", ""]
    if planted:
        out += [f"- **{caught} of the {planted} planted bugs**",
                f"- **{len(noisy)} of the {len(clean)} clean programs "
                f"flagged**",
                ""]
    else:
        out += ["No hand verdicts yet, so nothing is scored. A zero here "
                "would say assay found nothing, which is a different claim "
                "from nobody having looked.", ""]

    out += ["## Every Planted Bug", ""]
    for p in scored:
        out += [f"### {p.name}", "",
                f"{p.checks} checks, {p.flagged} flagged, "
                f"{p.caught} of {len(p.bugs)} planted bugs found.", "",
                "| bug | assay | which case |", "|---|---|---|"]
        for b in p.bugs:
            said = "found" if b.found else "missed"
            out.append(f"| {b.number} | {said} | {b.case or b.note or '-'} |")
        out.append("")

    out += ["## How the Set Was Built", "",
            "One harness and model wrote the ten programs from "
            "[`objectives.txt`](objectives.txt). A **different** harness and "
            "model put the bugs in, from the instruction in "
            "[`inject-prompt.txt`](inject-prompt.txt), which names no "
            "checker, no rule and no tool. Neither step was told assay "
            "exists.",
            "",
            "`generate.sh` and `inject.sh` are the two steps. Each broken "
            "program carries the injector's own `bugs.md` saying what it "
            "planted, and a `verdict.txt` recording, per bug, whether assay "
            "caught it and which case did.",
            "",
            "Whether a failing case *is* a given planted bug showing itself "
            "is a judgement, so it is made by hand and written down rather "
            "than matched by a script.",
            ""]

    (HERE / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")


#: The sentence the front page carries, between markers, so it is written by
#: the run and never by hand. Same shape as the 225's own headline.
HEADLINE = ("**assay found {caught} of the {planted} planted bugs and flagged "
            "{noisy} of the {clean} working originals.**")


def _write_headline(readme: Path, **counts: int) -> None:
    """Fill the marked block in the front-page README with this run."""
    if not readme.is_file():
        return
    text = readme.read_text(encoding="utf-8")
    opened, closed = "<!-- planted -->", "<!-- /planted -->"
    if opened not in text or closed not in text:
        return
    head, _, rest = text.partition(opened)
    _, _, tail = rest.partition(closed)
    readme.write_text(head + opened + "\n\n" + HEADLINE.format(**counts)
                      + "\n\n" + closed + tail, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=0,
                    help="only the first N of each, for a quick check")
    args = ap.parse_args()

    print("broken:")
    broken = sweep(HERE / "broken", True, args.limit)
    print("clean:")
    clean = sweep(HERE / "clean", False, args.limit)

    planted = sum(len(p.bugs) for p in broken)
    caught = sum(p.caught for p in broken)
    noisy = sum(1 for p in clean if p.flagged)
    print(f"\nassay found {caught} of {planted} planted bugs; "
          f"{noisy} of {len(clean)} clean programs flagged")

    stale = sum(len(p.stale) for p in broken)
    if stale:
        print(f"{stale} verdict(s) name a case that did not fail. Correct "
              f"verdict.txt before anything is written.", file=sys.stderr)
        return 1

    if not args.limit:
        write_readme(broken, clean)
        _write_headline(HERE.parent.parent / "README.md", caught=caught,
                        planted=planted, noisy=noisy, clean=len(clean))
        print("written: bench/planted/README.md and the front-page headline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
