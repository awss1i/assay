"""Test, resolve, fix, regress, until the plan passes.

The loop used to be model-driven and machine-refused. The model chose an action
each step and the machine said no: 438 refusals on record, and 32 of 35
investigations ended on "7 refused actions in a row": the run abandoned
because the model stopped proposing novel things to *read*, not because the
program worked. That is the exact inverse of what this factory already claims
for itself: *the machine owns the loop, the model answers one bounded question
per step.*

Here the machine owns it. It measures the artefact, derives a plan from what is
actually there, and **executes all of it**. The model is called when something
fails, and the question it is asked is bounded to one thing: this act produced
this measurement, the plan expected that, why, and what change fixes it.

That removes the whole class of failure where a run spends its budget choosing
what to look at, which is where the budget went.

It does not leave while a test fails. Not a count and not patience: the
exit condition is the plan passing. A failing case is localised by
construction, because the act names a control, the control names a handler and
the handler names a file, so there is always somewhere to aim. When a repair
stops being new the *lever* changes, and the last lever is always available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from assay import tint
from assay.surface import Case, Surface

LOG = logging.getLogger(__name__)

#: How a case came out. ``None`` means *could not tell*: no browser, or a
#: harness that died partway. It must never read as a failure, because recording a
#: check that did not happen as one that failed sends a repair after it.
PASSED, FAILED, UNKNOWN = "passed", "failed", "unknown"


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

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

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
        if self.detail:
            line += "\n" + tint.paint(f"    → {self.detail}", tint.RED,
                                      on=colour)
        return line


@dataclass
class Ladder:
    """What to try next for a case that will not come right.

    Every rung is a genuinely different request rather than the same one
    louder, which is what makes the loop bounded without a count: room, then
    the whole file rather than a window, then the failing function rewritten
    from its contract, then the module rewritten whole. The last rung is always
    available, so there is always a move. The one honest stop is a rewrite
    that reproduces a program already seen.
    """

    RUNGS = ("fix", "wider", "rewrite-function", "rewrite-module")

    at: int = 0

    @property
    def rung(self) -> str:
        return self.RUNGS[min(self.at, len(self.RUNGS) - 1)]

    @property
    def spent(self) -> bool:
        """Whether every different request has already been made."""
        return self.at >= len(self.RUNGS)

    def climb(self) -> None:
        self.at += 1

    def advice(self) -> str:
        """What this rung asks for, in the words the repair turn is given."""
        return {
            "fix": "Make the smallest change that fixes this.",
            "wider": ("The narrow fix did not work. Look at the whole file "
                      "rather than the failing line. The cause is very "
                      "likely somewhere the last edit did not touch, in how "
                      "this is wired up rather than in the line that threw."),
            "rewrite-function": ("Two narrower attempts failed. Rewrite the "
                                 "whole function this goes through, from what "
                                 "it is supposed to do, rather than patching "
                                 "it further."),
            "rewrite-module": ("Everything narrower has been tried. Rewrite "
                               "this file from its contract: what it must "
                               "export and what this case requires of it. "
                               "Keep every export other files depend on."),
        }[self.rung]


class QA:
    """Drive a plan against a workspace and repair whatever fails.

    Every hook is a callable so this module talks to no other part of the
    factory. Same arrangement the plan derivation uses, and for the same reason:
    the prompts and the mutations belong to the caller, and keeping them there
    is what makes this testable without a model.
    """

    def __init__(self, *, measure: Callable[[], Surface],
                 build_plan: Callable[[Surface], List[Case]],
                 carry_out: Callable[[Case], Result],
                 ask: Optional[Callable[..., Any]] = None,
                 apply: Optional[Callable[[Any, str], Any]] = None,
                 locate: Optional[Callable[[Case], str]] = None,
                 on_note: Optional[Callable[[str], None]] = None,
                 max_rounds: int = 0) -> None:
        self.measure = measure
        self.build_plan = build_plan
        self.carry_out = carry_out
        #: The repair path, and it is all or nothing: `ask` proposes a change
        #: and `apply` makes it. Without both, this measures and reports and
        #: never edits anything, which is what the command-line tool does.
        self.ask = ask
        self.apply = apply
        self.locate = locate or (lambda case: "")
        self.on_note = on_note or (lambda note: None)
        #: A backstop for the test suite alone, never a policy. Zero means the
        #: loop runs on its own condition, which is what a build does.
        self.max_rounds = max_rounds

        self.surface: Surface = Surface()
        self.plan: List[Case] = []
        self.results: Dict[str, Result] = {}
        self.ladders: Dict[str, Ladder] = {}
        #: Every repair proposed, so the same one twice is recognised before it
        #: costs an apply. Fingerprinted on the *change*, never on the reason,
        #: because rewording why does not make it a different edit.
        self.proposed: set = set()
        self.rounds = 0
        #: Whether the final full re-run has happened. See `run`.
        self._swept = False
        self.fixed: List[str] = []
        self.gave_up: List[str] = []

    # -- the loop ----------------------------------------------------------

    def run(self) -> "QA":
        """Measure, plan, execute, repair, regress. Leave when it passes."""
        self.surface = self.measure()
        self.plan = self.build_plan(self.surface)
        self.on_note(f"{len(self.plan)} case(s) to carry out")
        self._execute(self.plan)

        if self.apply is None or self.ask is None:
            # Nothing can repair anything, so there are no levers to spend and
            # no case to set aside. Running the loop here would put every
            # failure in `gave_up` without a single attempt, and report them
            # as unrepairable. A repair that was never tried must not read
            # like one that was tried and failed.
            return self

        while True:
            failing = self.to_attempt
            if not failing:
                # One clean sweep before leaving. Repairs re-run only the
                # case they were aimed at, so another case's verdict may be
                # older than the last change to the program, and a verdict
                # about code that has moved on is exactly what this loop
                # refuses everywhere else.
                if self.rounds and not self._swept:
                    self._swept = True
                    self._execute(self.plan)
                    continue
                return self
            if self.max_rounds and self.rounds >= self.max_rounds:
                return self
            self.rounds += 1
            if not self._attend(failing[0]):
                # Every lever spent on this one. Set it aside so the loop can
                # reach the others, and record it. A case abandoned in silence
                # is a hole one layer down from a program that ships broken.
                self.gave_up.append(failing[0].case.id)
        return self

    def _attend(self, result: Result) -> bool:
        """One repair attempt on one failing case. False when nothing is left."""
        case = result.case
        ladder = self.ladders.setdefault(case.id, Ladder())
        if ladder.spent:
            return False

        changes, why = self._ask_for_a_fix(result, ladder)
        if not changes:
            ladder.climb()
            return not ladder.spent

        mark = _fingerprint(changes)
        if mark in self.proposed:
            # The same edit twice is refused before it costs an apply. What has
            # run dry is this rung, not the case.
            self.on_note(f"{case.id}: that change was already tried")
            ladder.climb()
            return not ladder.spent
        self.proposed.add(mark)

        self._swept = False
        verdict = self.apply(changes, why)
        if not getattr(verdict, "applied", False) or not getattr(verdict, "improved", True):
            ladder.climb()
            return not ladder.spent

        # A repair invalidates every earlier verdict. The same experiment
        # against different code is a different experiment, so the whole plan
        # is carried out again, not only the case that was being fixed. That
        # is the regression half, and doing it per-case is how a fix for one
        # thing quietly breaks another.
        # The case it was aimed at first, and everything else only when that
        # one comes right. Regressing the whole plan after every kept change
        # is O(repairs x cases) browser launches, and a live build spent 54
        # minutes on 31 repairs doing it. A change that did not fix its
        # own case has almost certainly not fixed anybody else's. When it does
        # come right the full plan runs, and the loop cannot exit without a
        # clean sweep, so nothing is lost but the waiting.
        was_detail = result.detail
        before = {k: v.outcome for k, v in self.results.items()}
        self._execute([case])
        now = self.results.get(case.id)
        if now and not now.failed:
            self.on_note(f"{case.id}: fixed, re-testing everything")
            self._execute(self.plan)
        now = self.results.get(case.id)
        if now and not now.failed:
            self.fixed.append(case.id)
        elif now and now.detail == was_detail:
            # A change that landed and changed nothing is a spent rung.
            # Without this the ladder never climbs while the model keeps
            # proposing *novel* patches that each apply cleanly and fix
            # nothing. A live build took five kept changes on one criterion
            # and was still on the first rung. Progress here is the failure
            # *moving*, which is the same rule the rest of this factory ends
            # its loops on: something new, not something more.
            self.on_note(f"{case.id}: that change did not move the failure")
            ladder.climb()
        broke = [k for k, was in before.items()
                 if was == PASSED and self.results.get(k)
                 and self.results[k].failed]
        if broke:
            self.on_note("that fix broke: " + ", ".join(broke[:4]))
        return not ladder.spent

    def _execute(self, cases: Sequence[Case]) -> None:
        """Carry out every case and record what happened."""
        for case in cases:
            try:
                self.results[case.id] = self.carry_out(case)
            except Exception as exc:                    # a harness fault
                LOG.debug("case %s could not be carried out: %s", case.id, exc)
                self.results[case.id] = Result(
                    case=case, outcome=UNKNOWN,
                    detail=f"could not be carried out: {exc}")

    def _ask_for_a_fix(self, result: Result, ladder: Ladder):
        """One bounded question: this failed, here is where, what change fixes it.

        `ask(result, where, ladder)` answers with a mapping carrying
        `changes`, whatever `apply` takes, and `why`, a sentence for the
        record. Anything else is read as *no proposal*, which climbs the
        ladder rather than failing: a caller that cannot answer this rung
        gets asked the next one differently, and `ladder.advice()` is the
        wording that goes with it.
        """
        reply = self.ask(result, self.locate(result.case), ladder)
        if isinstance(reply, dict):
            return reply.get("changes"), str(reply.get("why") or result.case.what)
        return None, ""

    # -- what it established ------------------------------------------------

    @property
    def failing(self) -> List[Result]:
        """Every case that came out wrong, worst first.

        The contract before the rest: a criterion is what the program owes and
        a derived case is coverage, so a build that fails its contract is
        broken whatever else passes.

        **Every one of them, including the ones nothing could repair.** This
        used to hide those, because it was written for the repair loop, where
        it means *still worth another attempt*. As the thing a caller reads to
        find out what broke, that is a trap. `report.failing` came back empty
        about a program with eight failures. `to_attempt` is the repair loop's
        question and it can have its own name.
        """
        return sorted((r for r in self.results.values() if r.failed),
                      key=lambda r: (r.case.origin != "criterion", r.case.id))

    @property
    def to_attempt(self) -> List[Result]:
        """Failing cases the repair loop has not exhausted its levers on."""
        return [r for r in self.failing if r.case.id not in self.gave_up]

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
        return (f"{total} case(s) planned, {ran} carried out, "
                f"{ok} passed, {failed}"
                + (f", {len(self.fixed)} fixed on the way" if self.fixed else "")
                + (f", {len(self.gave_up)} could not be repaired"
                   if self.gave_up else ""))

    def render(self, colour: bool = False) -> str:
        """The whole record, in plan order.

        Plan order rather than failures-first: the sequence is the story of
        what was tried, and a case reads differently for what came before it.
        Colour is what makes the failures findable without reordering them.
        """
        out = [self.summary(colour), ""]
        for case in self.plan:
            r = self.results.get(case.id)
            out.append(r.render(colour) if r else tint.paint(
                f"{case.id} [not checked] {case.what}", tint.DIM, on=colour))
        return "\n".join(out)


def _fingerprint(changes: Any) -> str:
    """What a proposed change *is*, ignoring how it was described.

    Keyed on the edit rather than the reason: rewording why does not make it a
    different repair, and a loop that thinks it does will apply the same patch
    for ever.
    """
    import hashlib
    import json

    try:
        raw = json.dumps(changes, sort_keys=True, default=str)
    except (TypeError, ValueError):
        raw = repr(changes)
    return hashlib.sha256(" ".join(raw.split()).encode()).hexdigest()[:16]
