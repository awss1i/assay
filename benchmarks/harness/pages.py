"""Keep each set's headline counts, and write the results table from them.

Each scorer records its own set's counts in `results.json` after a complete
run. The results table in the front-page README and in the Benchmarks README
is then rewritten from every recorded set, so each number in it comes from a
run and neither scorer needs the other's results.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
REPO = BENCH.parent
RECORD = HERE / "results.json"

#: PyPI shows the front-page README and doesn't resolve relative links, so
#: its links are full URLs.
BLOB = "https://github.com/awss1i/assay/blob/main/benchmarks/"

#: Each set's row label and benchmark doc, in the order the table lists them.
SETS = {
    "generated": ("Pages written by AI", "generated.md"),
    "planted": ("Pages with planted bugs", "planted.md"),
}

#: The name of the marked block the table is written into.
BLOCK = "results"


def record(name: str, *, pages: int, bugs: int, found: int, working: int,
           flagged: int, path: Path = RECORD) -> None:
    """Save one set's counts from a complete run."""
    counts = _read(path)
    counts[name] = {"pages": pages, "bugs": bugs, "found": found,
                    "working": working, "flagged": flagged}
    path.write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")


def table(base: str = "", path: Path = RECORD) -> str:
    """The results table, with each set's name linked to its doc under `base`."""
    counts = _read(path)
    rows: List[str] = ["| Set | Pages | Bugs found | Working pages flagged |",
                       "|---|---|---|---|"]
    for name, (label, doc) in SETS.items():
        if name not in counts:
            continue
        one = counts[name]
        rows.append(f"| [{label}]({base}{doc}) | {one['pages']} | "
                    f"{one['found']} of {one['bugs']} | "
                    f"{one['flagged']} of {one['working']} |")
    return "\n".join(rows)


def write(path: Path = RECORD) -> List[Path]:
    """Rewrite the table in every page that carries it, and return those pages."""
    written = []
    for readme, base in ((REPO / "README.md", BLOB), (BENCH / "README.md", "")):
        if fill(readme, BLOCK, table(base, path)):
            written.append(readme)
    return written


def fill(page: Path, name: str, text: str) -> bool:
    """Put `text` between the `<!-- name -->` markers in a page.

    Blank lines separate it from the markers, because GitHub doesn't render
    markdown on the same line as an HTML comment.
    """
    if not page.is_file():
        return False
    was = page.read_text(encoding="utf-8")
    opened, closed = f"<!-- {name} -->", f"<!-- /{name} -->"
    if opened not in was or closed not in was:
        return False
    head, _, rest = was.partition(opened)
    _, _, tail = rest.partition(closed)
    page.write_text(head + opened + "\n\n" + text + "\n\n" + closed + tail,
                    encoding="utf-8")
    return True


def header(title: str, trail: List[tuple], about: str, here: Path) -> List[str]:
    """The centred block that opens a page, with the trail of pages above it.

    `trail` lists each level above the page as a name and the file it lives
    in, and `here` is the page being written, so each link is relative to it.
    The block is HTML because GitHub doesn't render markdown inside a centred
    paragraph.
    """
    links = [f'<a href="{_relative(to, here)}">{name}</a>' for name, to in trail]
    return [f'<h1 align="center">{title}</h1>',
            "",
            f'<p align="center">{" › ".join(links + [title])}</p>',
            "",
            f'<p align="center">{about}</p>',
            ""]


def _relative(to: Path, here: Path) -> str:
    return Path(os.path.relpath(to, here.parent)).as_posix()


def _read(path: Path) -> Dict[str, dict]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
