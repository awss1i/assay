"""Carry a plan out and keep what happened.

`QA` takes three callables: one that measures what the page offers, one that
derives a plan from that, and one that carries a single case out. It runs
every case, records each result, and answers the questions a caller asks of a
run: what failed, what could not be checked, and whether everything that
could be checked came out right.

It knows nothing about browsers, which is why it can be tested without one.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence

from assay import tint
from assay.surface import Case, Surface

LOG = logging.getLogger(__name__)

#: How a case came out. `UNKNOWN` means *could not tell*: no browser, or a
#: harness that died partway. It must never read as a failure, because
#: recording a check that did not happen as one that failed sends somebody
#: after a bug that is not there.
PASSED, FAILED, UNKNOWN = "passed", "failed", "unknown"

#: A case id, which is a position in the plan and never part of a finding's
#: name.
_IDS = re.compile(r"\b[CF]\d{3}\b")


@dataclass
class Result:
    """What happened when one case was carried out."""

    case: Case
    outcome: str = UNKNOWN
    #: What went wrong, in the numbers a reader can act on.
    detail: str = ""
    #: Everything measured, pass or fail. A criterion about *which way* a
    #: thing moved cannot be settled by the machine, and the reader needs the
    #: measurement rather than the verdict.
    evidence: str = ""
    #: Files this case left behind, by name: screenshots, dumps, anything a
    #: reader would want. Deliberately untyped and deliberately not called
    #: `screenshots`: this module knows nothing about browsers, and adding a
    #: browser word here would be the first thread of the tangle.
    artifacts: Dict[str, str] = field(default_factory=dict)
    #: Which rules this case broke, as short fixed names, in the order they
    #: fired. The detail is prose for a person. This is what a benchmark
    #: verdict or a grouping can hold on to without parsing it.
    rules: List[str] = field(default_factory=list)
    #: What the finding is about, when the case's own words do not say it:
    #: the token a page printed, the box whose example fails, the wiring
    #: that is wrong. Empty means `case.what` already names it.
    subject: str = ""
    #: The first uncaught exception this case saw, where it was thrown, and
    #: whether it was already thrown while the page loaded, before any act.
    crash_message: str = ""
    crash_frame: str = ""
    crash_at_load: bool = False
    #: Notes tying this finding to another. See `links`.
    links: List[Any] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

    @property
    def key(self) -> str:
        """The finding, named so that it survives the plan being renumbered.

        A case id is a position in the plan, and adding one case anywhere
        moves every id after it, so a verdict holding an id can end up
        crediting a different case without anything failing. The rule and
        what it was about are the same wherever the case lands.
        """
        rule = self.rules[0] if self.rules else self.outcome
        about = _IDS.sub("", self.subject or self.case.what)
        return f"{rule}@{' '.join(about.split())}"

    def render(self, colour: bool = False) -> str:
        """One case, as a line. Dim when it passed, red when it did not.

        A run of forty cases with two failures is a wall of identical lines,
        and colour is what makes the two visible without reading any of them.
        """
        mark = {PASSED: "ok", FAILED: "FAILED", UNKNOWN: "not checked"}
        tone = {PASSED: tint.GREEN, FAILED: tint.RED + tint.BOLD,
                UNKNOWN: tint.YELLOW}[self.outcome]
        line = (tint.paint(self.case.id, tint.DIM, on=colour) + " "
                + tint.paint(f"[{mark[self.outcome]}]", tone, on=colour) + " "
                + tint.paint(self.case.what,
                             *(() if self.failed else (tint.DIM,)), on=colour))
        # A repeat points at the first of its group instead of saying the
        # same sentence again, and everything else keeps its own detail.
        same = [one for one in self.links if one.kind == "same"]
        if self.detail and not same:
            line += "\n" + tint.paint(f"    → {self.detail}", tint.RED,
                                      on=colour)
        for one in self.links:
            line += "\n" + tint.paint(f"    ↳ {one.why}", tint.YELLOW,
                                      on=colour)
        return line


class QA:
    """Drive a plan against a page and keep what happened.

    Every hook is a callable, so this module talks to no other part of assay
    and can be exercised without a browser.
    """

    def __init__(self, *, measure: Callable[[], Surface],
                 build_plan: Callable[[Surface], List[Case]],
                 carry_out: Callable[[Case], Result]) -> None:
        self.measure = measure
        self.build_plan = build_plan
        self.carry_out = carry_out

        self.surface: Surface = Surface()
        self.plan: List[Case] = []
        self.results: Dict[str, Result] = {}
        #: What the page logged as errors and which requests failed, across
        #: every tab the run opened. Information only. See `cli.as_json`.
        self.console_errors: List[str] = []
        self.failed_requests: List[str] = []

    def run(self) -> "QA":
        """Measure, plan, and carry every case out."""
        self.surface = self.measure()
        self.plan = self.build_plan(self.surface)
        LOG.debug("%d case(s) to carry out", len(self.plan))
        self._execute(self.plan)
        return self

    def _execute(self, cases: Sequence[Case]) -> None:
        """Carry out every case and record what happened."""
        for case in cases:
            try:
                self.results[case.id] = self.carry_out(case)
            except Exception as exc:                    # a harness fault
                LOG.debug("case %s could not be carried out, %s", case.id, exc)
                self.results[case.id] = Result(
                    case=case, outcome=UNKNOWN,
                    detail=f"could not be carried out, {exc}")

    # -- what it established ------------------------------------------------

    @property
    def failing(self) -> List[Result]:
        """Every case that came out wrong, worst first.

        The contract before the rest. A criterion is what the program owes
        and a derived case is coverage, so a program that fails its contract
        is broken whatever else passes.
        """
        return sorted((r for r in self.results.values() if r.failed),
                      key=lambda r: (r.case.origin != "criterion", r.case.id))

    @property
    def unchecked(self) -> List[Result]:
        return [r for r in self.results.values() if r.outcome == UNKNOWN]

    @property
    def works(self) -> bool:
        """Whether every case that could be carried out came out right."""
        return not any(r.failed for r in self.results.values())

    def summary(self, colour: bool = False) -> str:
        """The line that says what was actually tested. Never a task count."""
        total = len(self.plan)
        ran = sum(1 for r in self.results.values() if r.outcome != UNKNOWN)
        ok = sum(1 for r in self.results.values() if r.outcome == PASSED)
        bad = sum(1 for r in self.results.values() if r.failed)
        failed = tint.paint(f"{bad} failed", tint.RED + tint.BOLD,
                            on=colour and bool(bad))
        same = sum(1 for r in self.results.values() if r.failed
                   and any(one.kind == "same" for one in r.links))
        return (f"{total} case(s) planned, {ran} carried out, "
                f"{ok} passed, {failed}"
                + (f" ({same} of them repeat an earlier finding)" if same else ""))

    def render(self, colour: bool = False) -> str:
        """The whole record, in plan order.

        Plan order rather than failures-first. The sequence is the story of
        what was tried, and a case reads differently for what came before it.
        Colour is what makes the failures findable without reordering them.
        """
        out = [self.summary(colour), ""]
        for case in self.plan:
            r = self.results.get(case.id)
            out.append(r.render(colour) if r else tint.paint(
                f"{case.id} [not checked] {case.what}", tint.DIM, on=colour))
        return "\n".join(out)
