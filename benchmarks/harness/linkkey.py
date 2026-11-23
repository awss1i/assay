"""Check the links a run draws between findings against a hand-written key.

assay links a repeated finding to the first one in its group, and links a
finding about the whole page to the case where the page threw while loading.
A wrong link hides one real problem behind another, so every link a run draws
on a benchmark program is checked against `links.txt`. A program with links
nobody has judged stops the scorer writing anything.

Each line of `links.txt` takes one of these forms.

    <program> same <finding key> -> <key of the first finding in its group>
    <program> load <finding key> -> <key of the case that threw on load>
    <program> none

`none` marks a program with several flags that a person judged should have no
links. Programs are named the way their scorer names them, for example
`dsh/30_paint2` or `planted/broken/06_tagfilter`, and `<marker>/broken/<name>`
for a set scored from its own folder. A set can keep its own `links.txt`
beside its programs.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

KEY = Path(__file__).resolve().parent / "links.txt"

Drawn = Tuple[str, str, str]

_LINE = re.compile(r"^(?P<program>\S+)\s+(?:(?P<none>none)|"
                   r"(?P<kind>same|load)\s+(?P<one>.+?)\s+->\s+(?P<other>.+))$")


def read(path: Path = KEY) -> Dict[str, Set[Drawn]]:
    """Read the key, mapping each judged program to its expected links."""
    out: Dict[str, Set[Drawn]] = {}
    if not path.is_file():
        return out
    for at, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        got = _LINE.match(line)
        if not got:
            raise ValueError(f"{path}:{at}: cannot read {line!r}")
        links = out.setdefault(got["program"], set())
        if not got["none"]:
            links.add((got["kind"], got["one"].strip(), got["other"].strip()))
    return out


def drawn(results: Sequence) -> Set[Drawn]:
    """The links a run drew, named by finding key rather than case id."""
    keys = {r.case.id: r.key for r in results}
    return {(one.kind, r.key, keys.get(one.to, one.to))
            for r in results for one in getattr(r, "links", [])}


class Marks:
    """Tallies how a set of programs' links compare with the key."""

    def __init__(self) -> None:
        self.drawn = 0
        self.right = 0
        self.wrong: List[Tuple[str, Drawn]] = []
        self.missed: List[Tuple[str, Drawn]] = []
        self.unjudged: List[str] = []

    def mark(self, program: str, links: Set[Drawn],
             key: Dict[str, Set[Drawn]]) -> None:
        """Compare one program's links with what the key says it should have."""
        self.drawn += len(links)
        if program not in key:
            if links:
                self.unjudged.append(program)
            return
        want = key[program]
        self.right += len(links & want)
        self.wrong += [(program, one) for one in sorted(links - want)]
        self.missed += [(program, one) for one in sorted(want - links)]

    def sentence(self) -> str:
        """A sentence giving the drawn, right, wrong and missing links."""
        return (f"assay drew {self.drawn} links between findings. "
                f"{self.right} of them match the answer key, "
                f"{len(self.wrong)} are wrong, and {len(self.missed)} that "
                f"the key expects are missing")
