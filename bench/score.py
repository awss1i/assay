"""Score assay against programs whose real state somebody established by hand.

    python bench/score.py bench

A checker nobody has checked is an opinion with a progress bar. This runs
assay over every cell of a suite and writes down two different things, which
are worth keeping apart:

**What each harness produced.** How many of its programs actually work. That
number comes from `truth.txt`, where a person opened each one and drove it,
and never from assay, because a leaderboard scored by the tool it is promoting
is not evidence of anything.

**How well assay judged them.** Its agreement with that hand truth, and the
two ways of disagreeing counted separately, because they do not cost the
same. Calling a working program broken sends whoever is holding it to edit
code that was right; calling a broken one working is a bug that got through.

A cell is `programs/<harness>/<model>/`, holding its own programs and its own
`truth.txt`. Cells are found by walking the tree rather than listed in a
manifest, so adding a harness or a model is a new folder and nothing else. A
list that must be edited in step with a directory is a list that ends up
disagreeing with it.

Every number this project publishes is written here. None is typed by hand
anywhere, because the one that was went stale within a day.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from assay import check  # noqa: E402


@dataclass
class Judged:
    """One program: what it is, what a person said, what assay said."""

    name: str
    truth: str
    why: str
    said: str = ""
    cases: int = 0
    failed: int = 0
    seconds: float = 0.0
    detail: str = ""

    @property
    def objective(self) -> str:
        return self.name.split("_", 1)[1] if "_" in self.name else self.name

    @property
    def agrees(self) -> bool:
        """Whether assay's finding matches the hand verdict.

        The two columns deliberately do not use the same word, because the
        two claims are not the same size. A person drove the program and
        read its source, and says it **works** or is **broken**. assay drove
        it once and either found something or did not, which is **flagged**
        or **clean**, and neither is a verdict on the program.

        It matters beyond tidiness: `flagged` is the word that makes the
        output safe to hand to a model. Told a page is broken, an agent goes
        and edits it; told what was pressed and what did not move, it goes
        and looks.
        """
        return (self.said == "flagged") == (self.truth == "broken")


@dataclass
class Cell:
    """One harness driving one model, over the whole objective list."""

    harness: str
    model: str
    folder: Path
    rows: List[Judged] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.harness} / {self.model}"

    @property
    def works(self) -> List[Judged]:
        return [r for r in self.rows if r.truth == "works"]

    @property
    def cried_wolf(self) -> List[Judged]:
        """Working programs assay called broken. The expensive mistake."""
        return [r for r in self.works if r.said and not r.agrees]

    @property
    def missed(self) -> List[Judged]:
        """Broken programs assay called working."""
        return [r for r in self.rows
                if r.truth == "broken" and r.said and not r.agrees]

    @property
    def scored(self) -> List[Judged]:
        return [r for r in self.rows if r.said]


def read_truth(cell: Path) -> Dict[str, tuple]:
    """The hand verdicts for one cell, or nothing if it has none yet."""
    path = cell / "truth.txt"
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, truth, why = (line.split(None, 2) + ["", ""])[:3]
        out[name] = (truth, why.strip())
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
    """Carry every program in one cell out, and record what assay said.

    `limit` takes the first few instead of all of them. That exists for the
    smoke run in CI: it proves this script still executes against the current
    assay, which the test suite does not. The tests can all pass while this
    file is broken, and the first person to find out would be a stranger
    trying to reproduce a published number.
    """
    verdicts = read_truth(cell.folder)
    programs = sorted(p for p in cell.folder.iterdir()
                      if p.is_dir() and (p / entry).is_file())
    if limit:
        programs = programs[:limit]

    for program in programs:
        truth, why = verdicts.get(program.name, ("", ""))
        row = Judged(name=program.name, truth=truth, why=why)
        cell.rows.append(row)
        if not truth:
            print(f"  {program.name:<16} no hand verdict yet, not scored")
            continue

        began = time.time()
        try:
            run = check(program, entry)
        except Exception as exc:                       # never lose the sweep
            row.detail = f"assay raised: {str(exc)[:70]}"
            print(f"  {program.name:<16} ERROR {row.detail}")
            continue

        row.said = "clean" if run.works else "flagged"
        row.cases = len(run.plan)
        row.failed = len(run.failing)
        row.seconds = time.time() - began
        if run.failing:
            row.detail = _trimmed(run.failing[0].detail)
        print(f"  {program.name:<16} {truth:<7} {row.said:<7} "
              f"{row.cases:>3} cases {row.failed:>3} failed "
              f"{row.seconds:>6.1f}s  {'ok' if row.agrees else 'XX'}")


def _trimmed(text: str, most: int = 150) -> str:
    """What assay said, short enough for a table cell and cut on a word.

    Mid-word truncation in a published table reads as carelessness about
    everything else on the page, which is the one impression this document
    cannot afford.
    """
    text = " ".join(text.split())
    if len(text) <= most:
        return text
    return text[:text.rfind(" ", 0, most)].rstrip(",;:") + "..."


def write_cell_results(suite: Path, cell: Cell) -> None:
    """The cell's own record, beside its own programs."""
    scored = cell.scored
    out = [f"# {cell.label}",
           "",
           f"{len(cell.rows)} programs, from the objectives in "
           f"`../../../objectives.txt`.",
           "",
           "`truth` is what a person established by opening the program and "
           "driving it. `assay` is what the tool said on its own. They are "
           "separate columns because the whole point is to compare them.",
           "",
           "| # | objective | truth | assay | agree | why the truth is what it is |",
           "|---|---|---|---|---|---|"]
    for r in cell.rows:
        number, _, _ = r.name.partition("_")
        out.append(f"| {number} | {r.objective} | {r.truth or '-'} | "
                   f"{r.said or '-'} | {'' if not r.said else ('ok' if r.agrees else '**XX**')} "
                   f"| {r.why} |")

    judged = [r for r in cell.rows if r.truth]
    if judged:
        out += ["",
                f"**What this pairing produced:** {len(cell.works)} of "
                f"{len(cell.rows)} programs work. Hand-established.",
                ""]
    else:
        out += ["",
                f"**Not yet judged.** These {len(cell.rows)} programs have "
                f"been generated but nobody has opened them yet, so there is "
                f"no truth to score against. A zero here would say they are "
                f"all broken, which is a different thing from not knowing.",
                ""]
    if scored:
        defects = len(cell.rows) - len(cell.works)
        out += ["**What assay found here:**",
                "",
                f"- {defects - len(cell.missed)} of the {defects} defects"
                + (f", missing {', '.join(r.name for r in cell.missed)}"
                   if cell.missed else ""),
                f"- {len(cell.cried_wolf)} false alarms across the "
                f"{len(cell.works)} working programs"
                + (f": {', '.join(r.name for r in cell.cried_wolf)}"
                   if cell.cried_wolf else "")]
    (cell.folder / "results.md").write_text("\n".join(out) + "\n")


def write_suite_readme(suite: Path, cells: List[Cell]) -> None:
    """The record, aggregated from the cells and never hand-edited.

    **It leads with what assay found, not with how often it agreed.**
    Agreement is the flattering number and it is close to meaningless on a
    corpus like this one: most pages work, so a tool that printed `clean`
    for everything and never opened a browser would agree with the answer
    key nine times out of ten. The two numbers that actually describe a
    checker are how much of what is there it finds, and how often it is
    right when it speaks, and neither can be had that way.

    The false alarms are named, one row each. A tool that lists its own by
    name is making a claim somebody can check, which is the only kind worth
    printing. Where each program came from still matters and is still
    recorded, because the strongest objection to any of this is that one
    corpus came from one place: three independent sources, one of them a
    bare API call with no agent at all, is the answer to that. It is a
    sentence, not a table.
    """
    objectives = [line.split("|", 1)[0]
                  for line in (suite / "objectives.txt").read_text().splitlines()
                  if line.strip()]
    every = [r for c in cells for r in c.scored]
    wolf = [r for c in cells for r in c.cried_wolf]
    miss = [r for c in cells for r in c.missed]
    works = sum(1 for r in every if r.truth == "works")
    judged = [r for c in cells for r in c.rows if r.truth]
    sources = ", ".join(sorted({c.harness for c in cells}))
    models = ", ".join(sorted({c.model for c in cells}))

    out = ["# The benchmark",
           "",
           "*Generated by `score.py`. Every number here was produced by "
           "running it; none is typed by hand.*",
           "",
           f"{len(judged)} programs, written to the {len(objectives)} "
           f"objectives in [`objectives.txt`](objectives.txt) by {sources} on "
           f"{models}. **A person opened every one of them and drove it**, "
           f"and that hand-written answer key is what assay is marked "
           f"against. It has no part in writing it.",
           "",
           f"**{len(judged) - works} of the {len(judged)} are broken.** "
           f"The rest work.",
           "",
           "## Contents",
           "",
           "- [What It Found](#what-it-found)",
           "- [What Is Wrong With the Broken Ones]"
           "(#what-is-wrong-with-the-broken-ones)",
           "- [Where the Programs Came From]"
           "(#where-the-programs-came-from)",
           ""]

    if every:
        defects = len(every) - works
        found = defects - len(miss)
        flags = found + len(wolf)
        out += ["## What It Found",
                "",
                f"- **{found} of the {defects} defects**",
                f"- **{len(wolf)} false alarms** across the {works} working "
                f"programs",
                ""]
        if flags:
            out += [f"So when assay reports a problem, it is a real one "
                    f"**{found} times out of {flags}**.",
                    ""]
        out += ["The two are counted apart because they do not cost the "
                "same. A miss leaves you where you started, which for a "
                "check costing nothing and usually taking under a minute is a "
                "fair price. "
                "A false alarm sends whoever is holding the program off to "
                "edit code that was right, which is the expensive one.",
                "",
                ("When it flags a working page, it " if wolf else
                 "It has never yet flagged a working page. If it does, it ")
                + "will not tell you the page is broken: it hands over what "
                "it did and what happened, and lets you look. If an agent is "
                "reading the output, same story.",
                "",
                f"There is no single accuracy figure here because it would "
                f"be meaningless: {works} of these {len(judged)} programs "
                f"work, so printing `clean` for everything and never opening "
                f"a browser scores "
                f"{round(100 * works / len(judged))}%.",
                ""]

    if wolf:
        out += ["## The false alarms, by name",
                "",
                "Every working program assay flagged, and what it said about "
                "it. Listed for the same reason the defects are: a number "
                "nobody can check is not evidence.",
                "",
                "| program | what assay said | why it is wrong |",
                "|---|---|---|"]
        for c in cells:
            for r in c.cried_wolf:
                out.append(f"| [`{c.harness}/{r.name}`]"
                           f"(programs/{c.harness}/{c.model}/{r.name}/"
                           f"index.html) | {r.detail} | {r.why} |")
        out.append("")

    broken = [(c, r) for c in cells for r in c.rows if r.truth == "broken"]
    if broken:
        out += ["## What Is Wrong With the Broken Ones",
                "",
                "Every program here is in this repository, so any row can "
                "be opened and disagreed with.",
                "",
                "| program | what is wrong | assay saw it |",
                "|---|---|---|"]
        for c, r in broken:
            out.append(f"| [`{c.harness}/{r.name}`]"
                       f"(programs/{c.harness}/{c.model}/{r.name}/index.html) "
                       f"| {r.why} | {'yes' if r.said == 'flagged' else '**no**'} |")
        out.append("")

    out += ["## Where the Programs Came From",
            "",
            "Three sources, kept apart so the corpus does not come from one "
            "place. They turn out to be barely distinguishable: a full agent "
            "loop, a different agent loop and a single unaided API call land "
            "within a program or two of each other, which is a finding about "
            "harnesses rather than about assay.",
            ""]
    for c in cells:
        judged_here = [r for r in c.rows if r.truth]
        made = (f"{len(c.works)} of {len(c.rows)} work" if judged_here
                else f"{len(c.rows)} not yet judged")
        out.append(f"- [`{c.harness}` on `{c.model}`]"
                   f"(programs/{c.harness}/{c.model}/results.md): {made}")

    out += ["", "---", "",
            "Reproduce all of this with `python bench/score.py`. It needs no "
            "key and no network: the programs are checked in, assay runs them "
            "in a browser and the verdicts come out the same.", ""]
    (suite / "README.md").write_text("\n".join(out) + "\n")


#: Where the top-level README keeps its generated numbers. A score typed by
#: hand goes stale the first time the corpus grows, and the one that was typed
#: by hand went stale within a day.
#:
#: The sentence goes on its own line between the markers, with blank lines
#: either side. Written hard against an inline HTML comment, GitHub stops
#: reading the rest of the line as markdown and the `**` shows up as two
#: asterisks.
HEADLINE = {
    "score2": ("**Across {total} pages checked by hand, assay found {found} "
               "of the {broken} real defects and raised {wolf} false "
               "alarms.** When it reports a problem it is a real one {found} "
               "times out of {flags}."),
}


def _write_headline(readme: Path, **counts: int) -> None:
    """Fill each marked block in the README with the run that just happened."""
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
    ap.add_argument("--cell", help="score only this harness/model")
    ap.add_argument("--entry", default="index.html")
    ap.add_argument("--limit", type=int, default=0, metavar="N",
                    help="only the first N programs of each cell, for a "
                         "smoke run that proves this script still works")
    args = ap.parse_args(argv)

    cells = find_cells(args.suite)
    if args.cell:
        cells = [c for c in cells if f"{c.harness}/{c.model}" == args.cell]
        if not cells:
            print(f"no such cell: {args.cell}", file=sys.stderr)
            return 2

    for cell in cells:
        print(f"\n== {cell.label}")
        run_cell(cell, args.entry, args.limit)
        if not args.limit:
            write_cell_results(args.suite, cell)

    # A partial run must not overwrite the record of a full one. The files in
    # the tree say "this is what happened"; three programs out of 75 is not
    # what happened, and CI writing that over it would be a lie told by a
    # green tick.
    every = [r for c in cells for r in c.scored]
    wolf = sum(len(c.cried_wolf) for c in cells)
    agreed = sum(1 for r in every if r.agrees)
    works = sum(1 for r in every if r.truth == "works")
    defects = len(every) - works
    found = defects - sum(len(c.missed) for c in cells)
    if not args.limit:
        write_suite_readme(args.suite, cells)
        _write_headline(args.suite.parent / "README.md", total=len(every),
                        found=found, broken=defects, wolf=wolf,
                        flags=found + wolf, works=works, agreed=agreed)
    print(f"\nassay found {found} of {defects} defects; "
          f"{wolf} false alarms across {works} working programs")
    if args.limit:
        print("smoke run, nothing written")
    else:
        print(f"written: {args.suite / 'README.md'} and each cell's results.md")
    return 0 if wolf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
