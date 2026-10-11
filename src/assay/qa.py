"""Run a plan and record the results.

`QA` takes three callables: one that measures what the page offers, one that
builds a plan from that, and one that carries out a single case. It runs every
case, records each result, and reports what failed, what couldn't be checked,
and whether every case that could be checked passed.

It never drives a browser itself, so it can be tested without one.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence

from assay import tint
from assay.surface import Case, Surface

LOG = logging.getLogger(__name__)

#: How a case came out. `UNKNOWN` means the case couldn't be checked, for
#: example because carrying it out raised an error. It never counts as a
#: failure, so nobody goes looking for a bug that isn't there.
PASSED, FAILED, UNKNOWN = "passed", "failed", "unknown"

#: A case id. It's a position in the plan, so `Result.key` strips it.
_IDS = re.compile(r"\b[CF]\d{3}\b")


@dataclass
class Result:
    """What happened when one case was carried out."""

    case: Case
    outcome: str = UNKNOWN
    #: What went wrong, with the numbers a reader can act on.
    detail: str = ""
    #: Everything measured, whether the case passed or failed. Some criteria,
    #: like which way a thing moved, need a reader to judge the measurement.
    evidence: str = ""
    #: Files the case left behind, by name, such as screenshots. The field
    #: stays generic because this module doesn't depend on the browser.
    artifacts: Dict[str, str] = field(default_factory=dict)
    #: Short fixed names of the rules this case broke, in the order they
    #: fired. `detail` is prose for a person, and benchmarks and grouping
    #: match on these instead.
    rules: List[str] = field(default_factory=list)
    #: What the finding is about when `case.what` doesn't say it, such as the
    #: token a page printed or the box whose example fails. Empty means
    #: `case.what` names it.
    subject: str = ""
    #: The first uncaught exception in this case, where it was thrown, and
    #: whether it was thrown while the page loaded, before any act.
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
        """A name for the finding that stays the same when the plan changes.

        Adding a case moves every case id after it, so a benchmark verdict
        that stored an id could silently credit the wrong case. The rule and
        its subject don't depend on position.
        """
        rule = self.rules[0] if self.rules else self.outcome
        about = _IDS.sub("", self.subject or self.case.what)
        return f"{rule}@{' '.join(about.split())}"

    def render(self, colour: bool = False) -> str:
        """One case as a line, coloured so failures stand out."""
        mark = {PASSED: "ok", FAILED: "FAILED", UNKNOWN: "not checked"}
        tone = {PASSED: tint.GREEN, FAILED: tint.RED + tint.BOLD,
                UNKNOWN: tint.YELLOW}[self.outcome]
        line = (tint.paint(self.case.id, tint.DIM, on=colour) + " "
                + tint.paint(f"[{mark[self.outcome]}]", tone, on=colour) + " "
                + tint.paint(self.case.what,
                             *(() if self.failed else (tint.DIM,)), on=colour))
        # A repeat shows its link to the first finding instead of repeating
        # the detail.
        same = [one for one in self.links if one.kind == "same"]
        if self.detail and not same:
            line += "\n" + tint.paint(f"    → {self.detail}", tint.RED,
                                      on=colour)
        for one in self.links:
            line += "\n" + tint.paint(f"    ↳ {one.why}", tint.YELLOW,
                                      on=colour)
        return line


class QA:
    """Run a plan against a page and record the results.

    Each step is a callable passed in, so the class runs without a browser.
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
        #: Console errors and failed requests across every tab the run opened.
        #: They're reported but never fail a case. See `cli.as_json`.
        self.console_errors: List[str] = []
        self.failed_requests: List[str] = []

    def run(self) -> "QA":
        """Measure, plan, and carry every case out."""
        self.surface = self.measure()
        self.plan = self.build_plan(self.surface)
        LOG.debug("cases to carry out: %d", len(self.plan))
        self._execute(self.plan)
        return self

    def _execute(self, cases: Sequence[Case]) -> None:
        """Carry out every case and record what happened."""
        for case in cases:
            try:
                self.results[case.id] = self.carry_out(case)
            except Exception as exc:            # recorded as unchecked
                LOG.debug("case %s couldn't be carried out, %s", case.id, exc)
                self.results[case.id] = Result(
                    case=case, outcome=UNKNOWN,
                    detail=f"couldn't be carried out, {exc}")

    @property
    def failing(self) -> List[Result]:
        """Every failed case, criteria first, then in plan order.

        A criterion is what the program has to do, so its failures come
        before failures of derived cases.
        """
        return sorted((r for r in self.results.values() if r.failed),
                      key=lambda r: (r.case.origin != "criterion", r.case.id))

    @property
    def unchecked(self) -> List[Result]:
        return [r for r in self.results.values() if r.outcome == UNKNOWN]

    @property
    def works(self) -> bool:
        """Whether every case that could be carried out passed."""
        return not any(r.failed for r in self.results.values())

    def summary(self, colour: bool = False) -> str:
        """One line counting cases planned, carried out, passed and failed."""
        total = len(self.plan)
        ran = sum(1 for r in self.results.values() if r.outcome != UNKNOWN)
        ok = sum(1 for r in self.results.values() if r.outcome == PASSED)
        bad = sum(1 for r in self.results.values() if r.failed)
        failed = tint.paint(f"{bad} failed", tint.RED + tint.BOLD,
                            on=colour and bool(bad))
        same = sum(1 for r in self.results.values() if r.failed
                   and any(one.kind == "same" for one in r.links))
        return (f"{total} {'case' if total == 1 else 'cases'} planned, "
                f"{ran} carried out, "
                f"{ok} passed, {failed}"
                + (f" ({same} of them repeat an earlier finding)" if same else ""))

    def render(self, colour: bool = False) -> str:
        """The summary and every case, in plan order.

        Failures stay in place so the record reads in the order things were
        tried. Colour makes them easy to find.
        """
        out = [self.summary(colour), ""]
        for case in self.plan:
            r = self.results.get(case.id)
            out.append(r.render(colour) if r else tint.paint(
                f"{case.id} [not checked] {case.what}", tint.DIM, on=colour))
        return "\n".join(out)
