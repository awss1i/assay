"""Link the findings in one run that repeat each other or follow a crash.

A page with one fault can fail many cases, like a row of tag chips that each
stay lit, or every case on a page that threw while loading. Every failure is
still reported, but the first of a group carries the detail and the rest point
at it. Nothing here changes a case's outcome. It adds notes to finished
results, in two situations:

- Two failures are the same finding when they share a rule, read the same
  once quoted text is removed, and are about controls in the same family,
  meaning their selectors match once positions are dropped. Named controls
  must also share a label, so the chips of one tag bar group together but an
  Undo and a Redo don't. A crash groups only with the same message thrown from
  the same place, because two handlers can throw the same message for
  different reasons.
- A finding about the whole page is noted as following a crash on load only
  when every case ran on a page that had already thrown the same error before
  anything was pressed. The note says when the crash happened and doesn't
  claim it caused the finding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

#: A selector's `:nth-child` position, which differs between otherwise
#: identical controls.
_POSITION = re.compile(r":nth-child\(\d+\)")

#: Text a finding quotes from the page, and its "first seen at" reference.
#: Both say where a fault showed up, so two findings that differ only in these
#: are the same fault in two places.
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_FIRST_SEEN = re.compile(r"[;,]?\s*first seen at [CF]\d{3}")

#: Rules about the page as a whole, which a crash on load can explain.
PAGE_WIDE = ("nothing-responds", "nothing-drawn")


@dataclass
class Link:
    """One note tying a finding to another."""

    #: `same` for a repeat of another finding, `load` for a finding about
    #: the whole page on a page that threw while loading.
    kind: str
    #: The case id it points at.
    to: str
    #: The sentence shown to the reader.
    why: str


def family(selector: str) -> str:
    """A selector with its positions removed, naming the kind of control."""
    return _POSITION.sub("", selector or "")


def _shape(detail: str) -> str:
    """A finding's detail with quoted text and back-references removed."""
    return " ".join(_QUOTED.sub("_", _FIRST_SEEN.sub("", detail)).split())


#: Kinds of control told apart by position rather than by name, like the
#: cells of a grid or the rows of a draggable list. Two in one family are the
#: same control in two places, whatever their labels.
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
    # A named control only matches one with the same label. An Undo and a
    # Redo in one toolbar share a family but are two controls.
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

    # Every case that opened the page. The run-level findings (`F` ids and
    # `C000`) have no acts and opened nothing.
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
