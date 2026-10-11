"""Score assay against programs a person has tested by hand.

    python bench/score.py bench

The scorer runs assay over every cell of the suite and records two results.

- How many of each harness's programs work. This comes from `truth.txt`,
  where a person opened and used each program, so it never depends on assay.
- How well assay judged them. That's the broken programs where it flagged
  the actual bug, and the working programs it flagged anyway. The two are
  counted separately because a false alarm sends someone to change code that
  was right, and a miss lets a bug through.

A broken program only counts as found when assay flagged its actual bug. A
flag for something else doesn't count. Deciding which finding is the bug takes
judgement, so it's written by hand in each cell's `verdicts.txt`, and every
flag on a broken program must be judged there before anything is written.

A cell is `programs/<harness>/<model>/`, holding its programs, `truth.txt` and
`verdicts.txt`. Cells are found by walking the tree, so adding a harness or a
model only needs a new folder.

Every published number for this set is written by this script, and only by a
complete run. A partial run (`--cell` or `--limit`) writes nothing.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from assay import check  # noqa: E402
import linkkey  # noqa: E402
from machine import machine, plural, timing  # noqa: E402

TRUTHS = ("works", "broken")


@dataclass
class Judged:
    """One program, with a person's verdict and assay's result."""

    name: str
    truth: str
    why: str
    said: str = ""
    cases: int = 0
    seconds: float = 0.0
    detail: str = ""
    error: str = ""
    #: Every failing case in this run, as `key -> case id`.
    failing: Dict[str, str] = field(default_factory=dict)
    #: `found` or `missed` for a broken program, from `verdicts.txt`.
    status: str = ""
    #: The findings the verdict names as the defect.
    defect: List[Tuple[str, str]] = field(default_factory=list)
    #: Flags the verdict names as something other than the defect.
    other: List[Tuple[str, str]] = field(default_factory=list)
    note: str = ""
    #: The links the run drew between its findings.
    links: set = field(default_factory=set)

    @property
    def objective(self) -> str:
        return self.name.split("_", 1)[1] if "_" in self.name else self.name

    @property
    def found(self) -> bool:
        """Whether the defect itself was flagged in this run."""
        return (self.truth == "broken" and self.status == "found"
                and any(key in self.failing for key, _ in self.defect))

    @property
    def stale(self) -> List[str]:
        """Keys the verdict names that did not fail in this run."""
        return [k for k, _ in self.defect + self.other
                if k not in self.failing]

    @property
    def unjudged(self) -> List[str]:
        """Failing keys on a broken program that nobody has judged."""
        if self.truth != "broken":
            return []
        named = {k for k, _ in self.defect + self.other}
        return [k for k in self.failing if k not in named]


@dataclass
class Cell:
    """The programs one harness and model wrote, and how each was judged."""

    harness: str
    model: str
    folder: Path
    rows: List[Judged] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.harness} / {self.model}"

    @property
    def scored(self) -> List[Judged]:
        return [r for r in self.rows if r.said]

    @property
    def works(self) -> List[Judged]:
        return [r for r in self.scored if r.truth == "works"]

    @property
    def broken(self) -> List[Judged]:
        return [r for r in self.scored if r.truth == "broken"]

    @property
    def cried_wolf(self) -> List[Judged]:
        """Working programs assay flagged, which are its false alarms."""
        return [r for r in self.works if r.said == "flagged"]

    @property
    def missed(self) -> List[Judged]:
        """Broken programs whose defect was not flagged."""
        return [r for r in self.broken if not r.found]

    @property
    def other_flags(self) -> List[Tuple[Judged, str, str]]:
        """Flags on broken programs that are not the defect."""
        return [(r, k, why) for r in self.broken for k, why in r.other]


def read_truth(cell: Path) -> Dict[str, tuple]:
    """Read one cell's `truth.txt`, or return nothing if it has none yet."""
    path = cell / "truth.txt"
    if not path.is_file():
        return {}
    out = {}
    for at, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, truth, why = (line.split(None, 2) + ["", ""])[:3]
        if truth not in TRUTHS:
            raise ValueError(f"{path}:{at}: {truth!r} isn't one of {TRUTHS}")
        out[name] = (truth, why.strip())
    return out


_VERDICT = re.compile(r"^(?P<name>\S+)\s+(?P<said>found|missed|other)\s*"
                      r"(?P<rest>.*)$")


def read_verdicts(cell: Path) -> Dict[str, dict]:
    """Read which finding is each broken program's defect from `verdicts.txt`.

    Each line takes one of these forms, and any other line raises ValueError.

        <program> found <key> | <note>    this flag is the defect
        <program> missed <note>           the defect was not flagged
        <program> other <key> | <note>    this flag is something else
    """
    path = cell / "verdicts.txt"
    out: Dict[str, dict] = {}
    if not path.is_file():
        return out
    for at, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        got = _VERDICT.match(line)
        if not got:
            raise ValueError(f"{path}:{at}: can't read {line!r}")
        one = out.setdefault(got["name"], {"status": "", "defect": [],
                                           "other": [], "note": ""})
        rest = got["rest"].strip()
        if got["said"] == "missed":
            if one["status"] == "found":
                raise ValueError(f"{path}:{at}: found and missed")
            one["status"], one["note"] = "missed", rest
            continue
        key, bar, note = rest.partition(" | ")
        if not bar or "@" not in key:
            raise ValueError(f"{path}:{at}: expected '<key> | <note>'")
        if got["said"] == "found":
            if one["status"] == "missed":
                raise ValueError(f"{path}:{at}: found and missed")
            one["status"] = "found"
            one["defect"].append((key.strip(), note.strip()))
        else:
            one["other"].append((key.strip(), note.strip()))
    return out


def find_cells(suite: Path) -> List[Cell]:
    """Every harness/model pair under the suite, in a stable order."""
    root = suite / "programs"
    cells = []
    for harness in sorted(p for p in root.iterdir() if p.is_dir()):
        for model in sorted(p for p in harness.iterdir() if p.is_dir()):
            cells.append(Cell(harness.name, model.name, model))
    return cells


def run_cell(cell: Cell, entry: str = "index.html",
             limit: int = 0) -> None:
    """Run assay on every program in one cell and record what it reported.

    `limit` keeps only the first few programs. CI uses it for a smoke run that
    checks this script still works against the current assay, which the test
    suite doesn't cover.
    """
    truths = read_truth(cell.folder)
    verdicts = read_verdicts(cell.folder)
    programs = sorted(p for p in cell.folder.iterdir()
                      if p.is_dir() and (p / entry).is_file())
    if limit:
        programs = programs[:limit]

    for program in programs:
        truth, why = truths.get(program.name, ("", ""))
        row = Judged(name=program.name, truth=truth, why=why)
        verdict = verdicts.get(program.name, {})
        row.status = verdict.get("status", "")
        row.defect = list(verdict.get("defect", []))
        row.other = list(verdict.get("other", []))
        row.note = verdict.get("note", "")
        cell.rows.append(row)
        if not truth:
            print(f"  {program.name:<16} no hand verdict yet, not scored")
            continue

        began = time.time()
        try:
            run = check(program, entry)
        except Exception as exc:
            row.error = f"assay raised: {str(exc)[:70]}"
            print(f"  {program.name:<16} ERROR {row.error}")
            continue

        row.seconds = time.time() - began
        row.said = "clean" if run.works else "flagged"
        row.cases = len(run.plan)
        row.failing = {r.key: r.case.id for r in run.failing}
        row.links = linkkey.drawn(list(run.results.values()))
        if run.failing:
            row.detail = _trimmed(run.failing[0].detail)
        mark = ("found" if row.found else "missed") \
            if truth == "broken" else ("ok" if row.said == "clean" else "XX")
        print(f"  {program.name:<16} {truth:<7} {row.said:<7} "
              f"{row.cases:>3} cases {len(row.failing):>3} failed "
              f"{row.seconds:>6.1f}s  {mark}")
        for key in row.stale:
            print(f"    !! the verdict names {key!r}, which didn't fail")
        for key in row.unjudged:
            print(f"    ?? {row.failing[key]} {key!r} failed and no verdict "
                  f"line says what it is")
        if truth == "broken" and not row.status:
            print("    ?? broken, and verdicts.txt says nothing about it")


def _trimmed(text: str, most: int = 150) -> str:
    """Shorten assay's message for a table cell, cutting at a word boundary."""
    text = " ".join(text.split())
    if len(text) <= most:
        return text
    return text[:text.rfind(" ", 0, most)].rstrip(",;:") + "..."


def _assay_said(r: Judged) -> str:
    """The table cell saying what assay made of this program."""
    if not r.said:
        return "-"
    if r.truth == "works":
        return "clean" if r.said == "clean" else "**flagged**"
    if r.found:
        return "found"
    return "flagged, not the bug" if r.failing else "**missed**"


def write_cell_results(cell: Cell) -> None:
    """Write the cell's `results.md` beside its programs."""
    out = [f"# {cell.label}",
           "",
           f"{len(cell.rows)} programs, from the objectives in "
           f"`../../../objectives.txt`.",
           "",
           "`truth` is what a person found by opening and using each "
           "program. `assay` is what the tool reported, and for a broken "
           "program, whether it flagged the actual bug, as judged by hand in "
           "[`verdicts.txt`](verdicts.txt).",
           "",
           "| # | objective | truth | assay | seconds | notes |",
           "|---|---|---|---|---|---|"]
    for r in cell.rows:
        number, _, _ = r.name.partition("_")
        out.append(f"| {number} | {r.objective} | {r.truth or '-'} | "
                   f"{_assay_said(r)} | "
                   f"{f'{r.seconds:.0f}' if r.said else '-'} | {r.why} |")

    out += ["",
            f"**Programs that work:** {len(cell.works)} of "
            f"{len(cell.scored)}, checked by hand.",
            "",
            "**What assay found:**",
            "",
            f"- the actual bug in {len(cell.broken) - len(cell.missed)} of "
            f"the {len(cell.broken)} broken programs"
            + (f", missing {', '.join(r.name for r in cell.missed)}"
               if cell.missed else ""),
            f"- {plural(len(cell.cried_wolf), 'false alarm')} across the "
            f"{len(cell.works)} working programs"
            + (f": {', '.join(r.name for r in cell.cried_wolf)}"
               if cell.cried_wolf else ""),
            f"- {plural(len(cell.other_flags), 'flag')} on broken programs "
            f"that aren't their bug"]
    (cell.folder / "results.md").write_text("\n".join(out) + "\n")


def _in_words(n: int) -> str:
    return {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
            6: "Six"}.get(n, str(n))


def write_suite_readme(suite: Path, cells: List[Cell],
                       measured_on: str) -> None:
    """Write the suite's `README.md` from every cell's results.

    The page leads with the bugs assay found instead of how often it agreed
    with the answer key. Most programs in the set work, so a tool that called
    everything clean without opening a browser would agree most of the time.
    """
    objectives = [line.split("|", 1)[0]
                  for line in (suite / "objectives.txt").read_text().splitlines()
                  if line.strip()]
    every = [r for c in cells for r in c.scored]
    works = [r for c in cells for r in c.works]
    broken = [(c, r) for c in cells for r in c.broken]
    wolf = [(c, r) for c in cells for r in c.cried_wolf]
    found = [r for _, r in broken if r.found]
    other = [(c, r, k, why) for c in cells for r, k, why in c.other_flags]
    flagged = [r for r in every if r.said == "flagged"]
    right = [r for r in flagged if r.found]
    harnesses = sorted({c.harness for c in cells})
    models = ", ".join(sorted({c.model for c in cells}))

    # The header is HTML so it can be centred, and markdown inside an HTML
    # block isn't rendered, so its links and code are HTML too.
    out = ['<h1 align="center">The generated benchmark</h1>',
           "",
           "---",
           "",
           '<p align="center"><i><code>score.py</code> writes this page, and '
           "every number here comes from running it. Which flag is a broken "
           "program's actual bug is judged by hand in each folder's "
           "<code>verdicts.txt</code>.</i></p>",
           "",
           f'<p align="center">{len(every)} programs, written to the '
           f'{len(objectives)} objectives in <a href="objectives.txt">'
           f"<code>objectives.txt</code></a> by {', '.join(harnesses)} on "
           f"{models}. A person opened and tested every one by hand, and "
           f"assay is scored against that answer key.</p>",
           "",
           f'<p align="center"><strong>{len(broken)} of the {len(every)} are '
           f"broken.</strong> The rest work.</p>",
           "",
           "---",
           "",
           "## Contents",
           "",
           "- [What assay Found](#what-assay-found)",
           "- [The Broken Programs](#the-broken-programs)",
           "- [Where the Programs Came From]"
           "(#where-the-programs-came-from)",
           "",
           "---",
           "",
           "## What assay Found",
           "",
           f"- **The actual bug in {len(found)} of the {len(broken)} broken "
           f"programs.** A flag on a broken program only counts if it's "
           f"that program's bug.",
           f"- **{plural(len(wolf), 'false alarm')}** on the {len(works)} working "
           f"programs.",
           f"- **{plural(len(other), 'flag')} on broken programs that aren't "
           f"their bug.**",
           ""]
    if flagged:
        out += [f"Of the {len(flagged)} programs assay flagged, "
                f"**{len(right)}** were flagged for their actual bug.", ""]
    out += [f"Per program, {timing([r.seconds for r in every])}. assay ran on "
            f"{measured_on}.",
            "",
            "Misses and false alarms are counted separately because a false "
            "alarm costs more. It sends someone to change code that was "
            "right.",
            "",
            f"There's no single accuracy percentage, because it would be "
            f"misleading. {len(works)} of these {len(every)} programs work, "
            f"so a tool that called everything clean without opening a "
            f"browser would score {round(100 * len(works) / max(len(every), 1))}%.",
            ""]

    if wolf:
        out += ["---",
                "",
                "## False Alarms",
                "",
                "| program | what assay said | why it's wrong |",
                "|---|---|---|"]
        out += [f"| [`{c.harness}/{r.name}`](programs/{c.harness}/{c.model}/"
                f"{r.name}/index.html) | {r.detail} | {r.why} |"
                for c, r in wolf]
        out.append("")

    if other:
        out += ["---",
                "",
                "## Flags That Are Not the Bug",
                "",
                "Flags on broken programs that were judged by hand to be "
                "something other than the program's bug.",
                "",
                "| program | finding | what it is |",
                "|---|---|---|"]
        out += [f"| `{c.harness}/{r.name}` | `{k}` | {why} |"
                for c, r, k, why in other]
        out.append("")

    if broken:
        out += ["---",
                "",
                "## The Broken Programs",
                "",
                "Every program is in this repository, so you can open any of "
                "them and check.",
                "",
                "| program | what is wrong | assay |",
                "|---|---|---|"]
        out += [f"| [`{c.harness}/{r.name}`](programs/{c.harness}/{c.model}/"
                f"{r.name}/index.html) | {r.why} | {_assay_said(r)} |"
                for c, r in broken]
        out.append("")

    out += ["---",
            "",
            "## Where the Programs Came From",
            "",
            f"{_in_words(len(harnesses))} sources, so the programs don't all "
            f"come from one tool.",
            ""]
    for c in cells:
        out.append(f"- [`{c.harness}` on `{c.model}`]"
                   f"(programs/{c.harness}/{c.model}/results.md): "
                   f"{len(c.works)} of {len(c.scored)} work")

    out += ["", "---", "",
            "Reproduce this with `python bench/score.py`. It needs no API "
            "key or network, because the programs are in the repository and "
            "assay runs them in a local browser.", ""]
    (suite / "README.md").write_text("\n".join(out) + "\n")


#: The sentence written into each marked block of the top-level README, by
#: marker name. Blank lines separate it from the markers, because GitHub
#: doesn't render markdown on the same line as an HTML comment.
HEADLINE = {
    "generated": (
        "assay found the real bug on {found} of the {broken} broken pages and "
        "flagged {wolf} of the {works} working pages. "
        "[Every page and result](https://github.com/awss1i/assay/blob/main/bench/README.md)."),
}


def _write_headline(readme: Path, **counts: object) -> None:
    """Fill each marked block in the README with this run's numbers."""
    if not readme.is_file():
        return
    text = readme.read_text()
    for name, wording in HEADLINE.items():
        opened, closed = f"<!-- {name} -->", f"<!-- /{name} -->"
        if opened not in text or closed not in text:
            continue
        head, _, rest = text.partition(opened)
        _, _, tail = rest.partition(closed)
        text = (head + opened + "\n\n" + wording.format(**counts)
                + "\n\n" + closed + tail)
    readme.write_text(text)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("suite", type=Path, nargs="?", default=Path(__file__).parent,
                    help="the benchmark folder (default: the one beside this script)")
    ap.add_argument("--cell", help="score only this harness/model, and write "
                                   "nothing")
    ap.add_argument("--entry", default="index.html")
    ap.add_argument("--limit", type=int, default=0, metavar="N",
                    help="only the first N programs of each cell, for a "
                         "smoke run that proves this script still works. It "
                         "writes nothing")
    args = ap.parse_args(argv)

    try:
        cells = find_cells(args.suite)
        if args.cell:
            cells = [c for c in cells if f"{c.harness}/{c.model}" == args.cell]
            if not cells:
                print(f"no such cell: {args.cell}", file=sys.stderr)
                return 2
        began = time.time()
        for cell in cells:
            print(f"\n== {cell.label}")
            run_cell(cell, args.entry, args.limit)
    except ValueError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    every = [r for c in cells for r in c.scored]
    works = sum(len(c.works) for c in cells)
    broken = sum(len(c.broken) for c in cells)
    found = broken - sum(len(c.missed) for c in cells)
    wolf = sum(len(c.cried_wolf) for c in cells)
    other = sum(len(c.other_flags) for c in cells)
    print(f"\nassay found {found} of {broken} defects, "
          f"{plural(wolf, 'false alarm')} across {works} working programs, "
          f"{plural(other, 'flag')} on broken programs that aren't the "
          f"defect, "
          f"{time.time() - began:.0f}s in all")

    marks = linkkey.Marks()
    key = linkkey.read()
    for c in cells:
        for r in c.scored:
            marks.mark(f"{c.harness}/{r.name}", r.links, key)
    print(f"links: {marks.sentence()}")
    for program, one in marks.wrong:
        print(f"  !! wrong link on {program}: {one}", file=sys.stderr)
    for program in marks.unjudged:
        row = next(r for c in cells for r in c.scored
                   if f"{c.harness}/{r.name}" == program)
        print(f"  ?? {program} drew links nobody has judged: "
              f"{sorted(row.links)}", file=sys.stderr)

    errors = [r for c in cells for r in c.rows if r.error]
    stale = sum(len(r.stale) for c in cells for r in c.rows)
    unjudged = sum(len(r.unjudged) for c in cells for r in c.rows) + sum(
        1 for c in cells for r in c.broken if not r.status)
    if errors or stale or unjudged or marks.wrong or marks.unjudged:
        print("Nothing is written until each of these is zero.\n"
              f"  programs that couldn't be checked: {len(errors)}\n"
              f"  verdict lines naming a finding that didn't fail: {stale}\n"
              f"  flags or broken programs with no verdict: {unjudged}\n"
              f"  programs whose links are wrong: {len(marks.wrong)}\n"
              f"  programs whose links aren't judged: {len(marks.unjudged)}",
              file=sys.stderr)
        return 1

    # Readers take the files in the tree as a complete run's results, so a
    # partial run mustn't overwrite them.
    if args.limit or args.cell:
        print("partial run, nothing written")
    else:
        measured_on = machine()
        for cell in cells:
            write_cell_results(cell)
        write_suite_readme(args.suite, cells, measured_on)
        seconds = [r.seconds for r in every]
        _write_headline(args.suite.parent / "README.md", total=len(every),
                        found=found, broken=broken, wolf=wolf, works=works,
                        grouping=marks.grouping(),
                        median=statistics.median(seconds),
                        fast=sum(1 for s in seconds if s < 60))
        print(f"written: {args.suite / 'README.md'} and each cell's results.md")
    return 0 if wolf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
