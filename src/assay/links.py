"""Which findings in one run are the same finding, and which follow a crash.

A page with one fault can fail a dozen cases. Eight tag chips that each stay
lit, eighteen cases that all ran on a page that threw on load. Every one of
those failures is true and every one is still reported, but a reader handed
them as twelve separate problems goes looking for twelve. This names the
repeats, so the first of each group carries the detail and the rest point at
it.

Nothing here changes what a case decided. It reads the finished results and
adds notes to them, and it is deliberately narrow about what it will join:

- **Same finding** means the same rule, the same words once the names in
  them are set aside, and controls from the same family, meaning selectors
  that match once their positions are dropped, so the chips of one tag bar group and an
  Undo and a Redo never do. A crash groups only with the same message thrown
  from the same place in the code, because two handlers can fail with the
  same message for different reasons.
- **The page threw while loading** is said of a finding about the whole page
  only when every case ran on a page that had already thrown, the same way,
  before anything was pressed. It is a fact about when the crash happened,
  not a guess about what caused what.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

#: A position in a selector, which is what separates one chip from the next.
_POSITION = re.compile(r":nth-child\(\d+\)")

#: Words a finding quotes from the page, and the case it points back to.
#: Both name *where*, not *what*, so two findings differing only in them are
#: the same finding in two places.
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_FIRST_SEEN = re.compile(r"[;,]?\s*first seen at [CF]\d{3}")

#: Findings about the page as a whole, which a crash on load can explain.
PAGE_WIDE = ("nothing-responds", "nothing-drawn")


@dataclass
class Link:
    """One note tying a finding to another."""

    #: `same` for a repeat of another finding, `load` for a finding about
    #: the whole page on a page that threw while loading.
    kind: str
    #: The case id it points at.
    to: str
    #: The sentence a reader sees.
    why: str


def family(selector: str) -> str:
    """A selector with the positions taken out, so it names the kind of control."""
    return _POSITION.sub("", selector or "")


def _shape(detail: str) -> str:
    """A finding's words with the names in them set aside."""
    return " ".join(_QUOTED.sub("_", _FIRST_SEEN.sub("", detail)).split())


#: Controls that are one of many by position rather than by name, the cells
#: of a grid, the rows of a list you drag. Two of these in one family are the
#: same control in two places whatever each is labelled.
POSITIONAL = ("cell", "handle", "radio", "checkbox")


def _who(result, controls: Dict[str, object]) -> Tuple[str, ...]:
    """Which control a finding is about, as far as sameness goes."""
    control = controls.get(result.case.control)
    if control is None:
        return (family(result.case.control),)
    kind = getattr(control, "kind", "")
    where = getattr(control, "family", "") or family(result.case.control)
    if kind in POSITIONAL:
        return (kind, where)
    # A named control is only the same as one with the same name. An Undo
    # and a Redo in one toolbar sit in one family and are two controls.
    return (kind, where, getattr(control, "label", ""))


def _sameness(result, controls: Dict[str, object]) -> Tuple[str, ...]:
    """What two results must share to be the same finding."""
    if "threw" in result.rules:
        return ("threw", result.crash_message, result.crash_frame)
    rule = result.rules[0] if result.rules else ""
    return (rule, _shape(result.detail)) + _who(result, controls)


def attach(results: Sequence,
           controls: Optional[Dict[str, object]] = None) -> None:
    """Add links to failed results, in plan order, in place.

    `results` is every result of the run in the order its cases were
    planned, and `controls` the controls the page offered, by selector. Only
    failed results are read or changed.
    """
    controls = controls or {}
    failed = [r for r in results if r.failed]
    anchors: Dict[Tuple[str, ...], object] = {}
    for r in failed:
        key = _sameness(r, controls)
        if not key[0]:
            continue
        first = anchors.setdefault(key, r)
        if first is not r:
            r.links.append(Link("same", first.case.id,
                                f"same finding as {first.case.id}"))

    # Every case that opened the page, which is every case in the plan. The
    # findings a run adds at the end carry no acts and opened nothing.
    ran = [r for r in results if not r.case.id.startswith(("F", "C000"))]
    crashed = [r for r in ran if r.crash_at_load]
    if not ran or len(crashed) != len(ran):
        return
    if len({(r.crash_message, r.crash_frame) for r in crashed}) != 1:
        return
    first = crashed[0]
    for r in failed:
        if r.rules and r.rules[0] in PAGE_WIDE:
            r.links.append(Link(
                "load", first.case.id,
                f"the page threw an error while loading ({first.case.id}), "
                f"before anything was pressed"))


def links_of(results: Sequence) -> List[Tuple[str, str, str, str]]:
    """Every link in a run, as `(from, kind, to, why)`."""
    return [(r.case.id, one.kind, one.to, one.why)
            for r in results for one in getattr(r, "links", [])]
