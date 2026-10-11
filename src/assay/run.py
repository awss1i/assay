"""Open a page, work out what it offers, use all of it, and report what broke.

Use it from Python like this::

    from assay import check
    report = check("./my-app")
    print(report.render())

The plan comes from what the page renders, so nothing needs a written test,
a baseline image, or a recording.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from assay import browser, links
from assay.qa import FAILED, PASSED, UNKNOWN, QA, Result
from assay.surface import Case, Surface, from_page, plan

#: The longest `browser.settle` waits for the page to stop changing. A page
#: that stops sooner returns sooner, so this only bounds pages that never
#: stop, like an endless feed. Reaching it is reported, not treated as a fault.
SETTLE_CEILING_MS = 15000

#: How many times `_one_look` polls for a change, and how far apart, before
#: the page-wide "nothing responds" finding is allowed. It's much longer than
#: a case waits, because a control that starts a slow job still works.
SLOW_LOOKS, SLOW_POLL_MS = 8, 500

#: How many times `_waited_out` reopens the page. A page can load differently
#: each time, and the finding it guards calls the whole page broken.
SLOW_TRIES = 3


@dataclass
class Opened:
    """A page as it was measured on load."""

    surface: Surface
    #: Uncaught exceptions. A page can call `console.error` and still work,
    #: but a throw stops the script, so anything measured after one comes
    #: from a page that had stopped running.
    crashes: List[str]
    console: List[str]
    failed_requests: List[str]
    title: str = ""
    #: How the page came to rest, as a `browser.Settled`.
    rest: Any = None
    #: Elements that look interactive but that the surface rules didn't pick
    #: up, counted by why they look interactive. Empty means the plan covers
    #: the whole page.
    unreached: Dict[str, int] = field(default_factory=dict)

    @property
    def blank(self) -> bool:
        """Whether the page shows nothing and offers nothing to work.

        Showing something means text, a loaded image or a painted canvas.
        Controls other than canvases also count, because a grid built from
        coloured `div`s shows none of those but its cells can be clicked.
        """
        return bool(self.rest is not None and self.rest.measured
                    and not self.rest.shown and not self.rest.named)

    @property
    def unmeasurable(self) -> bool:
        """Whether no reading of the page came back at all.

        A page that replaces a global the driver evaluates through, such as
        `eval`, makes every reading return nothing. That says nothing about
        whether the page works.
        """
        return bool(self.rest is not None and not self.rest.measured)


class Browser:
    """One browser and one server, kept open for a whole run.

    Each case opens a new tab, which gives it the page in its starting state
    and is much faster than launching a browser and a server per case.
    """

    def __init__(self, folder: Path, entry: str, headless: bool = True) -> None:
        self.folder, self.entry, self.headless = folder, entry, headless
        self._exit = contextlib.ExitStack()
        self._engine: Any = None
        self._play: Any = None
        self._base = ""
        #: How the last page opened came to rest, as a `browser.Settled`.
        self.rest = browser.Settled(True, 0, 0, 1, 0)

    def __enter__(self) -> "Browser":
        from playwright.sync_api import sync_playwright

        self._base = self._exit.enter_context(browser.serve(self.folder))
        self._play = sync_playwright().start()
        self._engine = self._play.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        return self

    def __exit__(self, *exc: Any) -> None:
        # Close the browser before stopping playwright. Unwinding both through
        # the ExitStack stops playwright first, which prints `Task was
        # destroyed but it is pending!` and a `TargetClosedError` after the
        # results.
        with contextlib.suppress(Exception):
            self._engine.close()
        with contextlib.suppress(Exception):
            self._play.stop()
        self._exit.close()

    @contextlib.contextmanager
    def open(self) -> Any:
        """Yield a new tab with the page loaded and settled, and its errors."""
        page = self._engine.new_page(viewport={"width": 1100, "height": 760})
        crashes: List[str] = []
        console: List[str] = []
        failed: List[str] = []
        browser.answer_dialogs(page)
        page.on("pageerror", lambda e: crashes.append(browser.crash(e)))
        page.on("console", lambda m: console.append(m.text[:200])
                if m.type == "error" else None)
        page.on("requestfailed",
                lambda r: failed.append(r.url.rsplit("/", 1)[-1][:120]))
        page.on("response", lambda r: failed.append(
            f"{r.url.rsplit('/', 1)[-1][:80]} -> HTTP {r.status}")
            if r.status >= 400 else None)
        try:
            page.goto(f"{self._base}/{self.entry.lstrip('/')}",
                      wait_until="load", timeout=30000)
            # `load` fires once the document and its scripts are fetched, which
            # on a framework-rendered page is before any control exists.
            self.rest = browser.settle(page, ceiling_ms=SETTLE_CEILING_MS)
            yield page, crashes, console, failed
        finally:
            with contextlib.suppress(Exception):
                page.close()


#: Suffixes that mark a path as a page, even when the file doesn't exist yet.
PAGES = (".html", ".htm", ".xhtml")


def aimed(where: str | Path, entry: str) -> Tuple[Path, str]:
    """Split a typed path into the folder to serve and the page to open.

    A file path gives both. Its folder is served, because a page loads its
    sibling files, and the file is the page to open. A path with a page
    suffix counts as a file even when it doesn't exist, so a missing
    `./todo.html` is reported as missing instead of being read as a folder.
    A directory is always served whole, with `entry` as the page.
    """
    aim = Path(where).expanduser()
    if aim.is_dir():
        return aim, entry
    if aim.is_file() or aim.suffix.lower() in PAGES:
        return aim.parent, aim.name
    return aim, entry


def look(folder: str | Path, entry: str = "index.html") -> Opened:
    """Open the page and measure what it offers, without running any cases."""
    root, entry = aimed(folder, entry)
    root = root.expanduser().resolve()
    with Browser(root, entry) as engine, engine.open() as (
            page, crashes, console, failed):
        surface = from_page(_Shot(browser.elements(page)))
        return Opened(surface=surface, unreached=browser.unreached(page),
                      crashes=list(crashes),
                      console=list(dict.fromkeys(console)),
                      failed_requests=list(dict.fromkeys(failed)),
                      title=(page.title() or ""), rest=engine.rest)


class _Shot:
    """The minimal input that `surface.from_page` reads."""

    def __init__(self, elements: Sequence[Any]) -> None:
        self.elements = list(elements)
        self.unavailable = ""


def judge(case: Case, before: Dict[str, Any], after: Dict[str, Any],
          crashes: Sequence[str], could_not: Sequence[str],
          was_off: Sequence[str], text: str, *, blank: bool = False,
          stirred: bool = False, self_stopped: bool = False,
          unmeasurable: bool = False, nothing_to_try: bool = False,
          answered_setup: Optional[bool] = None,
          answered_once: Optional[bool] = None,
          itself: Tuple[Optional[str], ...] = (None, None, None),
          page_back: Optional[bool] = None,
          elsewhere: Optional[bool] = None,
          lost: Sequence[str] = (),
          rows: Tuple[Any, Any] = (None, None)) -> Result:
    """Decide whether one case passed, with the evidence either way.

    Each rule is narrow because a broader version of it flagged working pages.
    """
    quiet = bool(case.expect.get("quiet"))
    bad: List[str] = []
    rules: List[str] = []

    def flag(rule: str, said: str) -> None:
        rules.append(rule)
        bad.append(said)

    # A page that replaces a global the driver evaluates through, such as a
    # function named `eval`, makes every reading return nothing. The result
    # is unknown, so a check that couldn't run is never reported as a failure.
    if unmeasurable:
        return Result(case=case, outcome=UNKNOWN,
                      detail="assay couldn't read this page, because the "
                             "page replaces a built-in function that assay "
                             "relies on (such as `eval` or `Function`). That "
                             "doesn't mean the page is broken",
                      evidence="")

    # A page that renders nothing would otherwise pass, because with no
    # controls its plan is a single case that only asserts nothing threw.
    # A drawing tool is also blank until something is drawn, so a blank page
    # fails a case only when it offers nothing to try, or when the case acted
    # and isn't `quiet`. `blank` describes the page after the case.
    if blank and (nothing_to_try or (case.acts and not quiet)):
        flag("blank", "the page shows nothing at all (no text, no images and "
                      "nothing drawn), so there's nothing to test")

    # An uncaught exception stops the page's script, so the rest of the case
    # ran against a page that had stopped.
    if crashes:
        flag("threw", f"the page threw an error and stopped running, "
                      f"{crashes[0]}")

    # Acts the page refused fail a case only when none of its acts could be
    # done. A canvas behind a "press Space to start" overlay can't be clicked,
    # and that's the page working. A `quiet` case never fails on them, because
    # it only asserts that nothing threw.
    if could_not and not quiet and len(could_not) >= len(case.acts or [None]):
        flag("could-not", "couldn't " + ", nor ".join(could_not[:3]))

    unpainted = browser.unpainted(after)
    if case.expect.get("painted") and unpainted:
        flag("unpainted", f"{unpainted} canvas still shows nothing after "
                          f"every step of this check" if unpainted == 1 else
                          f"{unpainted} canvases still show nothing after "
                          f"every step of this check")

    # The page saved these values in its own storage and was showing them, so
    # they should still be there after a reload.
    if lost:
        flag("forgot-on-reload",
             f"{' and '.join(repr(one) for one in lost[:2])} "
             f"{'was' if len(lost) == 1 else 'were'} saved in browser storage "
             f"by the page, but {'is' if len(lost) == 1 else 'are'} gone after "
             f"reloading it")

    want = str(case.expect.get("want") or "")
    if want and want.lower() not in (text or "").lower():
        flag("missing-text", f"the page doesn't contain {want!r}")

    acted = bool(case.acts)
    shifted = browser.moved(before, after)
    # Cases with their own rule (`again`, `same_each`) compare two acts with
    # each other, so the general "did anything change" rules skip them.
    own_rule = any(case.expect.get(k) for k in ("again", "same_each"))

    # A page that ran and stopped on its own, like a snake game that hit a
    # wall, can ignore key presses afterwards and still be working. It's only
    # flagged when its own text says what to press, like "Press Space to
    # restart", and pressing that key changed nothing.
    promised = browser.told_to_press(text)
    asked = browser.was_pressed(promised, case.acts)

    if (acted and not quiet and not case.expect.get("unchanged")
            and not own_rule and not stirred
            and browser.aimed_at_canvas(case.acts)
            and browser.canvas_still(before, after)):
        flag("canvas-unchanged",
             "the canvas this check clicked didn't change, even if other "
             "parts of the page did")
    elif (acted and shifted is False and not quiet
          and not case.expect.get("unchanged") and not own_rule
          and not was_off and not stirred
          and not (self_stopped and not asked)):
        flag("told-to-press" if asked else "no-change",
             f"the page says to press {promised}, but pressing {promised} "
             f"changes nothing" if asked
             else "nothing on the page changed at all")
    elif case.expect.get("unchanged") and shifted is True:
        flag("changed-when-still",
             "the page changed when it was supposed to stay as it was")

    # A row was removed but the pressed row is still on screen, so the wrong
    # row went, like a delete that splices at the wrong index. Seeing this
    # needs two rows, which is why the plan fills the page first.
    was_row, now_row = rows
    # Only when the pressed row's text is unique, because otherwise a
    # surviving row with the same text looks like the pressed one.
    alike = (was_row or {}).get("all") or []
    told_apart = alike.count((was_row or {}).get("text")) == 1
    if (was_row and now_row and was_row.get("text") and told_apart
            and int(now_row.get("many") or 0) < int(was_row.get("many") or 0)
            and was_row["text"] in (now_row.get("all") or [])):
        flag("wrong-row", f"this removed a row, but not the one it belongs "
                          f"to, and {was_row['text'][:60]!r} is still there")


    # `same_each` presses one control twice. `answered_once` is what the
    # first press did, and `before` and `after` bracket the second. A control
    # that ignores the first press and reacts to the second is one press
    # late, whatever its label says.
    if case.expect.get("same_each"):
        # With `itself`, the clicked element is judged as well as the page. A
        # scheduler cell with inverted styling stays plain on the first click
        # and looks booked on the second, while a summary line changes the
        # page both times. A thumbnail that opens a lightbox doesn't change on
        # either press, which is fine, so only a difference between the two
        # presses is a fault.
        was, now, back = (list(itself) + [None, None, None])[:3]
        if case.expect.get("itself") and was is not None and now is not None:
            # The element itself has to change on the second press. A key on
            # an on-screen keyboard never changes itself, so counting only the
            # page change flagged every key as one press late.
            if was == now and back is not None and back != now \
                    and shifted is True:
                flag("one-behind-cell",
                     "when clicked twice, this didn't change on the first "
                     "click and did on the second, so it reacts one press "
                     "late")
            # The element changed on the first press and changed back on the
            # second, but the page didn't return to where it started, like a
            # tag that switches off while its list stays filtered. `elsewhere`
            # is False when the second press changed nothing outside the
            # element and its wrappers. A tree folder that collapses its
            # subfolders on closing redraws them on the second press, so it
            # isn't flagged.
            elif (was != now and back == was and page_back is True
                  and elsewhere is False):
                flag("went-back",
                     "clicking this twice switched it back off, but the rest "
                     "of the page didn't change back, so what the first "
                     "click did is still in effect")
        elif answered_once is False and shifted is True:
            flag("one-behind",
                 "when pressed twice from the same starting point, this "
                 "changed nothing on the first press and changed the page on "
                 "the second, so it reacts one press late")
        first = "changed the page" if answered_once else "did nothing"
        second = browser.changed(before, after) or "nothing changed"
        return Result(case=case, outcome=FAILED if bad else PASSED,
                      detail=_sentences(bad)[:400], rules=rules,
                      evidence=f"the first press {first}. On the second, {second}"[:400])

    # `again` draws a second stroke after a first one that drew. The first
    # stroke is setup, so `before` already holds its marks. A canvas that
    # ignored the first stroke, like a chart, isn't asked about the second.
    if case.expect.get("again") and answered_setup:
        if shifted is False:
            flag("second-stroke",
                 "the first line drawn on this canvas appeared, but a second "
                 "line drawn elsewhere did not, so the canvas stopped "
                 "accepting drawing")

    # `was_off` holds acts skipped because the target was `disabled`. They go
    # in the evidence and stop the no-change rule above from firing, because
    # disabling a control is a deliberate choice by the page. A quantity box
    # with `max="10"` clamps 25 to 10 and disables `+`, which is correct. The
    # cost is missing a control that's disabled by mistake.
    observed = browser.changed(before, after)
    if was_off:
        observed += (", " if observed else "") + (
            f"the program has {was_off[0]} disabled")
    if could_not and not bad:
        observed += (", " if observed else "") + (
            "couldn't " + could_not[0] + ", and the rest of the case went ahead")

    return Result(case=case, outcome=FAILED if bad else PASSED,
                  detail=_sentences(bad)[:400], evidence=observed[:400],
                  rules=rules)


def _sentences(parts: Sequence[str]) -> str:
    """Join findings into one detail, capitalising each one after the first.

    Findings start lowercase so they can follow a case name, as in
    `--one-line` output. Every one after the first starts a new sentence.
    """
    return ". ".join(p if i == 0 else p[:1].upper() + p[1:]
                     for i, p in enumerate(parts))


def _text(page: Any) -> str:
    """The page's visible text, or an empty string if it can't be read."""
    with contextlib.suppress(Exception):
        return page.inner_text("body")[:3000]
    return ""


def _shoot(page: Any, into: Optional[Path], name: str) -> str:
    """Save a full-page screenshot into `into` and return its file name.

    Returns an empty string when `into` is None or the screenshot fails. It
    captures the full page because a viewport-sized shot often cuts off what
    failed.
    """
    if into is None:
        return ""
    try:
        into.mkdir(parents=True, exist_ok=True)
        path = into / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        return path.name
    except Exception:
        return ""


def _kept(into: Optional[Path], before: str, after: str) -> Dict[str, str]:
    """Which of a case's screenshots to keep, by label.

    When the before and after files are identical, the after file is deleted
    and the one left is labelled as unchanged.
    """
    if not (into and before and after):
        return {k: v for k, v in (("before", before), ("after", after)) if v}
    first, second = into / before, into / after
    try:
        if first.read_bytes() == second.read_bytes():
            second.unlink(missing_ok=True)
            return {"unchanged by this": before}
    except OSError:
        pass
    return {"before": before, "after": after}


def _seeding(cases: Sequence[Case]) -> List[Dict[str, str]]:
    """The acts of the shortest planned case that fills a form and submits it.

    The planner has already worked out what to type into which field and
    which button submits it, so the acts are reused instead of rebuilt.
    """
    submits = [c for c in cases
               if c.expect.get("changes") and c.acts
               and any("fill" in act for act in c.acts)
               and any("click" in act for act in c.acts)]
    if not submits:
        return []
    return list(min(submits, key=lambda c: len(c.acts)).acts)


#: A second value for each sample input, so the two seeded rows differ.
_SECOND = {"Sample item": "Another item",
           "someone@example.com": "nobody@example.com",
           "https://example.com/page": "https://example.com/other",
           "2026-03-14": "2026-03-21", "09:30": "10:45",
           "2026-03-14T09:30": "2026-03-21T10:45", "2026-03": "2026-04",
           "2026-W11": "2026-W12", "555-0100": "555-0199", "3:30": "4:15"}


def _twice(seed: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    """The seed acts, then the same acts again with different values.

    Two rows with the same text can't show which one a delete removed.
    """
    again = []
    for act in seed:
        said = str(act.get("fill", ""))
        if "=" not in said:
            again.append(dict(act))
            continue
        box, _, value = said.partition("=")
        if value.strip().isdigit():
            other = str(int(value.strip()) + 1)
        else:
            said = value.strip()
            other = _SECOND.get(said, (said + " two").strip())
        again.append({"fill": f"{box}={other}"})
    return list(seed) + again


def _once_there_is_data(was: Surface, now: Surface,
                        seed: Sequence[Dict[str, str]],
                        criteria: Sequence[Case]) -> List[Case]:
    """Cases for controls that only appear once the page holds data.

    A to-do list at load is a text box and a button, and its checkboxes,
    Delete buttons and item count only exist once there's a row. The page is
    filled and submitted twice, because a Delete that removes the wrong row
    needs two rows to show it. The planner then runs on the grown surface,
    and each case for a new control is kept with the filling in front of it,
    so it can run from a freshly loaded page.
    """
    had = {c.selector for c in was.controls}
    fresh = [c for c in now.controls if c.selector not in had]
    if not fresh:
        return []
    grown = {c.selector for c in fresh}
    out = []
    for case in plan(now, criteria):
        if case.control and case.control in grown and case.acts:
            out.append(Case(
                id=case.id, what=f"{case.what}, with two saved",
                acts=_twice(seed) + list(case.acts),
                expect=dict(case.expect), origin="seeded",
                control=case.control))
    return out


def check(folder: str | Path, entry: str = "index.html",
          criteria: Sequence[Case] = (),
          shots: Optional[Path] = None) -> QA:
    """Measure the page, plan cases, run them, and return the report.

    `shots` is a folder for a before and an after screenshot of each case.
    Without it nothing is written to disk and the run is a little faster.
    """
    # Read the path the same way the command line does, so
    # `check("./todo.html")` and `assay ./todo.html` open the same page.
    root, entry = aimed(folder, entry)
    root = root.expanduser().resolve()
    with Browser(root, entry) as engine:
        with engine.open() as (page, crashes, console, failed):
            opened = Opened(surface=from_page(_Shot(browser.elements(page))),
                            unreached=browser.unreached(page),
                            crashes=list(crashes),
                            console=list(dict.fromkeys(console)),
                            failed_requests=list(dict.fromkeys(failed)),
                            title=(page.title() or ""), rest=engine.rest)
        cases = plan(opened.surface, criteria)
        seed = _seeding(cases)
        #: Every control the page offered on load or after seeding, by
        #: selector. `links.attach` uses it to group failures by control.
        offered = {c.selector: c for c in opened.surface.controls}
        if seed:
            with contextlib.suppress(Exception):
                with engine.open() as (page, *_):
                    browser.perform(page, _twice(seed))
                    page.wait_for_timeout(300)
                    grown = from_page(_Shot(browser.elements(page)))
                    kept = browser.saved(page, _plainly(_twice(seed)))
                for c in grown.controls:
                    offered.setdefault(c.selector, c)
                cases += _once_there_is_data(opened.surface, grown, seed,
                                             criteria)
                if kept:
                    # The page saved the entries in its own storage, so they
                    # should survive a reload. Only values that were both
                    # saved and showing are checked.
                    cases.append(Case(
                        id="", what="save two, reload, and they're still "
                                    "there",
                        acts=_twice(seed) + [{"reload": "page"}],
                        expect={"survives": kept, "quiet": True},
                        origin="seeded"))
        for n, case in enumerate(cases, 1):
            case.id = f"C{n:03d}"
        # A blank page with nothing to press, type into or draw on can't
        # change, so `judge` can fail it straight away.
        nothing_to_try = not (opened.surface.operable
                              or opened.surface.canvases)

        #: IDs of the cases that saw the page change. `Result.evidence` can't
        #: tell you this, because it's a description and never empty.
        answered: set = set()
        #: Per measurement, whether any canvas held a picture. It's judged
        #: across the run, because a chart may only draw after a different
        #: case fills the field beside it.
        drew: List[bool] = []
        #: Facts the page showed about itself, each with the first case that
        #: saw it, so each is reported once however many cases see it.
        noticed: Dict[str, Tuple[str, str]] = {}
        #: Per control, whether pressing it ever changed the page. A missing
        #: key means the control was never pressed, which differs from
        #: pressed with no change.
        worked: Dict[str, bool] = {}
        #: Whether the page changes on its own, measured once per run, because
        #: seeing a once-a-second clock tick takes longer than a case waits.
        ticking: List[Optional[bool]] = [None]
        #: One reading per case of how many items are shown and what each
        #: displayed number says. Telling a number that counts the list from
        #: one that matches it once takes readings in several states.
        counts: List[Dict[str, Any]] = []
        #: Readings from before and after each case's final acts, so a number
        #: can be seen following the list up but not down.
        swings: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        #: The case id, typed values and page reading for each case that typed
        #: and submitted something. They're judged at the end, because which
        #: classes form a list is only known once it's been seen at more than
        #: one size.
        entries: List[Tuple[str, List[str], Dict[str, Any]]] = []
        #: Console errors and failed requests from every tab. They're reported
        #: as information and never decide a result, because a page can log an
        #: error and still work.
        heard: List[Tuple[List[str], List[str]]] = [
            (opened.console, opened.failed_requests)]
        #: Each case's crash list, and how many crashes had happened by the
        #: time the page finished loading.
        crashed: Dict[str, Tuple[List[str], int]] = {}

        def carry_out(case: Case) -> Result:
            with engine.open() as (page, crashes, console, failed):
                heard.append((console, failed))
                crashed[case.id] = (crashes, len(crashes))
                before = browser.signature(page)
                shot_before = _shoot(page, shots, f"{case.id}-before")
                # A case is judged on its last act, not on its typing.
                # Filling a field changes the page, so a case that types and
                # then presses a dead Add button would pass on the typing
                # alone. When every act before the last is a fill, pick or
                # choose, those acts run as setup and `before` is measured
                # after them. Canvas cases keep all their acts in the
                # measurement, because the click, drag and key sequence is
                # what's being tested. The second-stroke case (`again`) runs
                # its first stroke as setup, so that stroke's marks are in
                # `before`.
                fills_first = (len(case.acts) > 1
                               and (all("fill" in a or "pick" in a
                                        or "choose" in a
                                        for a in case.acts[:-1])
                                    or case.expect.get("again")))
                # `again` and `second` cases use only their first act as
                # setup. The acts after it are alternative attempts, and
                # running them as setup would put their marks in `before`.
                setup, final = (
                    (case.acts[:1], case.acts[1:])
                    if case.expect.get("again") or case.expect.get("second")
                    else (case.acts[:-1], case.acts[-1:]) if fills_first
                    else ([], case.acts))
                # Wait for an animating canvas to stop before acting, so any
                # change afterwards comes from the acts. Otherwise a game that
                # plays itself changes whatever is pressed. The second-stroke
                # case needs this too, or a moving game looks like a canvas
                # that drew the first stroke.
                wants_rest = (case.expect.get("changes")
                              or case.expect.get("again"))
                rested = (browser.settle_canvas(page)
                          if wants_rest and (before.get("canvas") or [])
                          else browser.Rested(False, False))
                itself_before = (browser.itself(page, case.control)
                                 if case.expect.get("itself") else None)
                was_quiet = rested.quiet
                # The canvas was moving when the watch began and then stopped
                # on its own.
                self_stopped = rested.quiet and rested.moved
                if was_quiet:
                    before = browser.signature(page)
                if case.expect.get("again") and not was_quiet:
                    # The canvas is still animating, so no change can be put
                    # down to a stroke and the case has nothing to judge.
                    return Result(case=case, outcome=PASSED, detail="",
                                  evidence="this canvas keeps changing on its "
                                           "own, so assay can't tell a drawn "
                                           "line from the animation")

                # `same_each` is measured between its two presses, because a
                # control that only reacts to the second press looks fine
                # when measured across both.
                if case.expect.get("same_each"):
                    setup_acts = case.acts[:-2]
                    if (len(setup_acts) == 2
                            and all("drag" in a for a in setup_acts)):
                        # Two strokes are setup for a control like Undo,
                        # which should take back one step per press. If the
                        # second stroke drew nothing, a correct Undo spends
                        # its first press on an empty step and looks one press
                        # late, so that rule is skipped and the evidence says
                        # why. A canvas that ignores strokes is the
                        # second-stroke case's job.
                        cn, wo = browser.perform(page, setup_acts[:1])
                        one_stroke = browser.signature(page)
                        cn2, wo2 = browser.perform(page, setup_acts[1:])
                        could_not, was_off = cn + cn2, wo + wo2
                        two_strokes = browser.signature(page)
                        if browser.canvas_still(one_stroke, two_strokes):
                            if browser.moved(before, one_stroke):
                                answered.add(case.id)
                            drew.append(_drew(one_stroke))
                            # The other rules still apply, so a crash is
                            # still reported.
                            result = judge(
                                case, one_stroke, two_strokes, crashes,
                                could_not, was_off, _text(page),
                                unmeasurable=opened.unmeasurable)
                            result.evidence = ("the second line drew "
                                               "nothing, so there was no "
                                               "second step to undo")
                            result.artifacts = _kept(
                                shots, shot_before,
                                _shoot(page, shots, f"{case.id}-after"))
                            return result
                    else:
                        could_not, was_off = browser.perform(page, setup_acts)
                    first_from = browser.signature(page)
                    # Both `itself` rules compare the page before and after a
                    # press, so a page that changes on its own, like a clock,
                    # always looks changed. `settle_canvas` only watches
                    # canvases, so the page is watched while idle instead,
                    # once per run.
                    watched = bool(case.expect.get("itself"))
                    if watched and ticking[0] is None:
                        # Long enough to see a once-a-second clock tick.
                        page.wait_for_timeout(1200)
                        ticking[0] = bool(browser.moved(
                            first_from, browser.signature(page)))
                        first_from = browser.signature(page)
                    ticks = bool(ticking[0])
                    itself_one = (browser.itself(page, case.control)
                                  if watched else None)
                    more, off_more = browser.perform(page, case.acts[-2:-1])
                    after_one = browser.signature(page)
                    itself_two = (browser.itself(page, case.control)
                                  if watched else None)
                    outside_two = (browser.outside(page, case.control)
                                   if watched else None)
                    more2, off2 = browser.perform(page, case.acts[-1:])
                    itself_three = (browser.itself(page, case.control)
                                    if watched else None)
                    outside_three = (browser.outside(page, case.control)
                                     if watched else None)
                    could_not = list(could_not) + list(more) + list(more2)
                    was_off = list(was_off) + list(off_more) + list(off2)
                    answered_once = browser.moved(first_from, after_one)
                    after = browser.signature(page)
                    if answered_once or browser.moved(after_one, after):
                        answered.add(case.id)
                    drew.append(_drew(after_one) or _drew(after))
                    # `after_one` and `after` bracket the second press. The
                    # `itself` readings show the element before the first
                    # press and after each press.
                    result = judge(
                        case, after_one, after, crashes, could_not, was_off,
                        _text(page), answered_once=answered_once,
                        # A page that changes on its own never returns to
                        # where it started, so it gets no readings, which
                        # switches both `itself` rules off.
                        itself=((itself_one, itself_two, itself_three)
                                if not ticks else (None, None, None)),
                        page_back=(browser.moved(first_from,
                                                 browser.signature(page))
                                   if not ticks else None),
                        elsewhere=(outside_two != outside_three
                                   if not ticks and outside_two is not None
                                   and outside_three is not None else None),
                        unmeasurable=opened.unmeasurable)
                    result.artifacts = _kept(
                        shots, shot_before,
                        _shoot(page, shots, f"{case.id}-after"))
                    return result

                could_not, was_off = browser.perform(page, setup)
                answered_setup = None
                if setup:
                    at_start, before = before, browser.signature(page)
                    answered_setup = browser.moved(at_start, before)
                    shot_before = _shoot(page, shots, f"{case.id}-before")
                # `before` and `after` bracket the whole case, so a page that
                # changed and then changed back looks as if it ignored the
                # case, like a palette that outlines a shape on one click and
                # removes the outline on the next. With more than one final
                # act, the page is compared after each act and `stirred`
                # records any change.
                was_counted = browser.counted(page)
                row_before = None
                stirred = False
                if len(final) > 1:
                    could_not_more, was_off_more = [], []
                    # Record which press in the sequence changed the page,
                    # for `_opposites_disagree`. A control like Previous only
                    # does something on a fresh page after Next.
                    seen = before
                    for at, step in enumerate(final):
                        # Seeded cases fill the page themselves, so the row
                        # is read after the filling and before the last press.
                        if at == len(final) - 1:
                            # Re-read the counts just before the last act. A
                            # seeded case fills the page and then presses
                            # Delete, so measured end to end the list grew
                            # and the removal is hidden.
                            was_counted = browser.counted(page)
                            # Only for a seeded case about one control. When
                            # a case clicks two cells, the first click can
                            # remove a row and change which row the second
                            # selector matches.
                            if case.control and case.origin == "seeded":
                                row_before = browser.row_of(page,
                                                            case.control)
                            # Record each submission's typed values against
                            # the list with both seeded rows in it. With one
                            # row, a running total equals the amount, so a
                            # row showing the total instead can't be spotted.
                            # Each submission is checked on its own, so a
                            # second one the page rejected isn't read as the
                            # first one's values going missing.
                            if case.origin == "seeded" and was_counted:
                                for half in (case.acts[:len(seed)],
                                             case.acts[len(seed):
                                                       2 * len(seed)]):
                                    typed = _plainly(half)
                                    if typed:
                                        entries.append((case.id, typed,
                                                        was_counted))
                        cn, wo = browser.perform(page, [step])
                        could_not_more += list(cn)
                        was_off_more += list(wo)
                        now = browser.signature(page)
                        _did_something(step, browser.moved(seen, now), worked)
                        seen = now
                        if not stirred and browser.moved(before, now):
                            stirred = True
                else:
                    could_not_more, was_off_more = browser.perform(page, final)
                could_not = list(could_not) + list(could_not_more)
                was_off = list(was_off) + list(was_off_more)
                after = browser.signature(page)
                # A canvas that paints on a timer may not have drawn yet,
                # because `settle` only watches the set of controls. Waiting
                # can only turn an empty canvas into a drawn one, so a canvas
                # that stays blank still fails.
                if case.expect.get("painted") and browser.unpainted(after):
                    page.wait_for_timeout(1200)
                    after = browser.signature(page)
                # Some pages submit a field on Enter and have no submit
                # button. When a `changes` case with setup changed nothing,
                # press Enter in the last field it filled and measure again.
                # This can only turn a failure into a pass.
                if (case.expect.get("changes") and setup
                        and browser.moved(before, after) is False):
                    with contextlib.suppress(Exception):
                        typed = setup[-1].get("fill", "").split("=")[0]
                        page.focus(typed)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(500)
                        after = browser.signature(page)
                if was_quiet and browser.moved(before, after) is False:
                    # The canvas was still before the acts and the page hasn't
                    # changed since. Wait once more in case the response is on
                    # a timer.
                    page.wait_for_timeout(900)
                    after = browser.signature(page)
                itself_after = (browser.itself(page, case.control)
                                if case.expect.get("itself") else None)
                lost = (browser.missing_from(page, case.expect["survives"])
                        if case.expect.get("survives") else [])
                shot_after = _shoot(page, shots, f"{case.id}-after")
                text = _text(page)
                # Read after the case, not at load, because a canvas can be
                # empty until something is done to it.
                now = browser.rendered(page)
                still_blank = bool(now is not None and not now["shown"]
                                   and not now["named"])
                _noted(browser.facts(page), case, noticed)
                row_after = (browser.rows_now(page,
                                              str(row_before.get("holder")),
                                              str(row_before.get("shape")))
                             if row_before else None)
                seen = browser.counted(page)
                if seen:
                    counts.append(seen)
                if was_counted and seen:
                    swings.append((was_counted, seen))
                if case.expect.get("changes") and seen:
                    typed = _plainly(case.acts)
                    if typed:
                        entries.append((case.id, typed, seen))
                if len(final) == 1:
                    _did_something(final[0], browser.moved(before, after),
                                   worked)
                if browser.moved(before, after) or answered_setup:
                    answered.add(case.id)
                drew.append(_drew(before) or _drew(after))
                result = judge(case, before, after, crashes, could_not,
                               was_off, text, answered_setup=answered_setup,
                               stirred=stirred, self_stopped=self_stopped,
                               blank=still_blank,
                               itself=(itself_before, itself_after),
                               rows=(row_before, row_after),
                               unmeasurable=opened.unmeasurable,
                               nothing_to_try=nothing_to_try, lost=lost)
                result.artifacts = _kept(shots, shot_before, shot_after)
                return result

        run = QA(measure=lambda: opened.surface, build_plan=lambda _: cases,
                 carry_out=carry_out)
        run.run()
        run.console_errors = list(dict.fromkeys(
            line for console, _ in heard for line in console))
        run.failed_requests = list(dict.fromkeys(
            line for _, failed in heard for line in failed
            if "favicon.ico" not in line))
        _unfillable_boxes(run, engine)
        _page_says(run, noticed)
        _opposites_disagree(run, opened.surface, worked)
        _counts_wrong(run, counts)
        _never_shown(run, counts, entries)
        _follows_one_way(run, counts, swings)
        # The page-wide "nothing responds" finding needs the whole page to
        # have loaded, so it's skipped when `settle` hit its ceiling. A page
        # that loads its list after a delay can settle on an idle machine and
        # still be loading on a busy one, and the result mustn't depend on
        # machine load.
        if opened.rest is None or opened.rest.quiet:
            _nothing_responds(run, answered, engine, opened.unreached)
        _nothing_drawn(run, any(drew), opened)
    for case_id, (crashes, at_load) in crashed.items():
        result = run.results.get(case_id)
        if result is not None and crashes:
            result.crash_message = str(crashes[0])
            result.crash_frame = getattr(crashes[0], "frame", "")
            result.crash_at_load = at_load > 0
    links.attach([run.results[c.id] for c in run.plan if c.id in run.results],
                 offered)
    return run


def _finding(run: QA, what: str, rule: str, detail: str, *,
             subject: str = "", evidence: str = "",
             page_wide: bool = False) -> None:
    """Record a finding about the whole run under its own id.

    These findings aren't acts someone could repeat, so they're numbered
    apart from the plan. `F` ids are facts the page showed while it was used,
    and `C000` is the verdict about the page as a whole. Each finding takes
    the first free id, so two findings never overwrite each other.
    """
    at = "C000" if page_wide and "C000" not in run.results else ""
    n = 1
    while not at:
        at = f"F{n:03d}" if f"F{n:03d}" not in run.results else ""
        n += 1
    case = Case(id=at, what=what, acts=[], expect={})
    run.plan.append(case)
    run.results[at] = Result(case=case, outcome=FAILED, detail=detail,
                             evidence=evidence, rules=[rule], subject=subject)


#: A typed value that arithmetic can use.
_A_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def _typed_junk(case: Case) -> bool:
    """Whether this case typed something other than a number into a field.

    A temperature converter given `Sample item` correctly shows `NaN`, so a
    computed-value finding after such a case would blame the page for what
    assay typed. An empty value doesn't count as junk.
    """
    for act in case.acts:
        value = str(act.get("fill") or act.get("enter") or "")
        if "=" not in value:
            continue
        said = value.partition("=")[2].strip()
        if said and not _A_NUMBER.match(said):
            return True
    return False


def _noted(seen: Dict[str, Any], case: Case,
           noticed: Dict[str, Tuple[str, str]]) -> None:
    """Keep each fact once, against the first case that showed it.

    Facts are read after every case, because a page can be fine on load and
    go wrong once it's used. The first case to show a fact is the way to
    reproduce it.
    """
    if not _typed_junk(case):
        for bad in seen.get("computed") or []:
            noticed.setdefault(f"computed:{bad.get('token')}",
                               (case.id, str(bad.get("around") or "")))
    # Wiring and ARIA facts come from the markup, so they count whatever was
    # typed.
    for why in seen.get("wiring") or []:
        noticed.setdefault(f"wiring:{why}", (case.id, why))
    for why in seen.get("aria") or []:
        noticed.setdefault(f"aria:{why}", (case.id, why))


#: Label words that reverse each other, so a page offering both claims one
#: control undoes the other. `on` and `off` are left out because a toggle is
#: often labelled with the state it will switch to.
_OPPOSITES = (
    ("next", "previous"), ("next", "prev"), ("forward", "back"),
    ("forward", "backward"), ("undo", "redo"), ("up", "down"),
    ("increase", "decrease"), ("more", "less"), ("plus", "minus"),
    ("add", "remove"), ("add", "delete"), ("expand", "collapse"),
)

#: The words in a label, without emoji or punctuation.
_WORDS = re.compile(r"[a-z]+")


#: Typed values a page should show exactly as typed. Long values and ones
#: with quotes or other symbols are left out, because a page can correctly
#: trim or escape them.
_PLAIN = re.compile(r"^[\w .@:/-]{2,40}$")

#: Dates and times as a field holds them. A page can show `2026-03-14` as
#: `14 March`, so these aren't expected to appear as typed.
_DATED = re.compile(r"^\d{4}-\d{2}(-\d{2})?(T\d{2}:\d{2})?$|^\d{2}:\d{2}$"
                    r"|^\d{4}-W\d{2}$")


def _plainly(acts: Sequence[Dict[str, str]]) -> List[str]:
    """The values this case typed that a page could be expected to echo."""
    out = []
    for act in acts:
        said = str(act.get("fill", "")).partition("=")[2].strip()
        if said and _PLAIN.match(said) and not _DATED.match(said):
            out.append(said)
    return out


def _lists_in(counts: Sequence[Dict[str, Any]]) -> set:
    """Classes whose count varies across the run, which marks them as lists.

    Requiring two items on screen at once would miss the common case of a
    list that goes from empty to one item.
    """
    every = {name for seen in counts for name in (seen.get("classes") or {})}
    return {name for name in every
            if len({int((seen.get("classes") or {}).get(name) or 0)
                    for seen in counts}) > 1}


def _never_shown(run: QA, counts: List[Dict[str, Any]],
                 entries: List[Tuple[str, List[str], Dict[str, Any]]]) -> None:
    """Flag a typed value that a list accepted but doesn't show in the new row.

    A page doesn't always have to show what it accepted. A sign-up form
    correctly hides the password. A row in a list exists to show what went
    into it, so this only checks pages with a list, which is why it runs at
    the end. A list is a class or a set of table rows whose count changed
    during the run.
    """
    lists = _lists_in(counts)
    # Table rows often have no class, so their count is checked separately.
    rows_vary = len({int(seen.get("rows") or 0) for seen in counts}) > 1
    if not lists and not rows_vary:
        return
    for case_id, typed, seen in entries:
        held = int(seen.get("rows") or 0) + sum(
            int((seen.get("classes") or {}).get(name) or 0) for name in lists)
        if held < 1:
            continue
        shown = str(seen.get("rowText") or "") + " " + " ".join(
            str((seen.get("texts") or {}).get(name) or "") for name in lists)
        gone = [one for one in typed if one not in shown]
        if not gone or len(gone) == len(typed):
            # A row missing every typed value is probably showing something
            # else entirely, not losing one field, so it isn't flagged.
            continue
        _finding(run, "values typed into a list show up in the new row",
                 "never-shown",
                 f"{', '.join(repr(one) for one in gone[:2])} was typed in "
                 f"and accepted, but the new row in the list doesn't show "
                 f"it, first seen at {case_id}",
                 evidence=shown[:300])
        return


def _did_something(step: Dict[str, str], moved: Optional[bool],
                   worked: Dict[str, bool]) -> None:
    """Record whether pressing this control was seen to change the page."""
    target = str(step.get("click") or step.get("dblclick") or "")
    if not target or moved is None:
        return
    worked[target] = worked.get(target, False) or bool(moved)


def _opposites_disagree(run: QA, surface: Optional[Surface],
                        worked: Dict[str, bool]) -> None:
    """Flag one of a reversing pair that never works while the other does.

    A single button may do nothing visible, like a palette swatch that sets
    the colour without showing a border. A page offering Next and Previous,
    where Next changed the page and Previous never did, has a fault. Two
    labels form a pair when they differ by exactly one word and that word
    pair is in `_OPPOSITES`.

    Both orders are planned because Previous does nothing on a freshly loaded
    page, so its fair test is the press after Next.
    """
    if surface is None:
        return
    named = [c for c in surface.operable
             if c.kind in ("button", "link") and c.label]
    for a in named:
        for b in named:
            if a.selector == b.selector:
                continue
            if worked.get(a.selector) is not True:
                continue
            if worked.get(b.selector) is not False:
                continue
            if not _reverses(a.label, b.label):
                continue
            _finding(run, f"{b.label} works as well as {a.label}",
                     "opposites",
                     f"{a.label} changed the page, but {b.label} never did, "
                     f"even right after {a.label}. "
                     f"As a pair, {b.label} should reverse what {a.label} "
                     f"does")
            return


def _how_many(seen: Dict[str, Any], lists: Sequence[str]) -> int:
    """How many items one reading showed.

    It takes the largest repeated thing, not the sum, because a row contains
    its own parts. A bookmark's title and link repeat as often as the
    bookmark, so adding them would count each row three times.
    """
    classes = seen.get("classes") or {}
    return max([int(seen.get("rows") or 0)]
               + [int(classes.get(name) or 0) for name in lists])


def _counts_wrong(run: QA, counts: List[Dict[str, Any]]) -> None:
    """Flag a number that moves with the list but isn't zero when it's empty.

    A number counts the list when its value minus the list size is the same
    in every reading. Being off by a constant isn't enough on its own, so
    the finding also needs a reading where the list is empty and the number
    isn't zero. Only whole numbers are read, because money and other
    decimals aren't counts.
    """
    if len(counts) < 3:
        return
    lists = _lists_in(counts)
    sized = [(_how_many(seen, lists),
              {str(n.get("at")): int(n.get("is"))
               for n in seen.get("numbers") or []
               if n.get("is") is not None})
             for seen in counts]
    if len({size for size, _ in sized}) < 2:
        return
    for at in set().union(*(set(seen) for _, seen in sized)):
        pairs = [(size, seen[at]) for size, seen in sized if at in seen]
        if len({size for size, _ in pairs}) < 2 or len(pairs) < 3:
            continue
        offsets = {said - size for size, said in pairs}
        if len(offsets) != 1:
            continue
        off = offsets.pop()
        empty = [said for size, said in pairs if size == 0]
        if off == 0 or not empty or empty[0] == 0:
            continue
        _finding(run, "the count of items matches the list",
                 "count-off",
                 f"a number on this page goes up and down by one with the "
                 f"list, so it counts the list, but it shows {empty[0]} when "
                 f"the list is empty. It's {off:+d} off at every size",
                 evidence=("the number reads " + ", ".join(
                     f"{said} with {size} shown"
                     for size, said in sorted(pairs)))[:300])
        return


def _said(seen: Dict[str, Any]) -> Dict[str, str]:
    """Each displayed number's text, as written on the page."""
    return {str(n.get("at")): str(n.get("said"))
            for n in seen.get("numbers") or []}


def _follows_one_way(run: QA, counts: List[Dict[str, Any]],
                     swings: List[Tuple[Dict[str, Any], Dict[str, Any]]]
                     ) -> None:
    """Flag a number that changes when the list grows but not when it shrinks.

    An expense tracker that doesn't re-total on delete is the example. The
    number has to change every time the list grew and never when it shrank,
    with at least one of each. Unlike `_counts_wrong`, money counts here,
    because this only asks whether the number moved, not whether it equals
    the list size.
    """
    # There's no check for a repeated class, because table rows usually have
    # none. `_how_many` counts table rows as well.
    lists = _lists_in(counts)
    up: Dict[str, List[bool]] = {}
    down: Dict[str, List[bool]] = {}
    for was, now in swings:
        change = _how_many(now, lists) - _how_many(was, lists)
        if change == 0:
            continue
        said_was, said_now = _said(was), _said(now)
        for at in set(said_was) & set(said_now):
            (up if change > 0 else down).setdefault(at, []).append(
                said_was[at] != said_now[at])
    for at, grew in up.items():
        shrank = down.get(at) or []
        if not grew or not shrank or not all(grew) or any(shrank):
            continue
        _finding(run, "a total that follows the list also goes down",
                 "one-way",
                 f"a number on this page changed every time the list grew "
                 f"({len(grew)} times) but never when it shrank "
                 f"({len(shrank)} times), so it stops following the list "
                 f"when items are removed")
        return


def _reverses(one: str, other: str) -> bool:
    """Whether two labels differ by exactly one word that reverses."""
    a, b = set(_WORDS.findall(one.lower())), set(_WORDS.findall(other.lower()))
    left, right = a - b, b - a
    if len(left) != 1 or len(right) != 1:
        return False
    was, now = left.pop(), right.pop()
    return (was, now) in _OPPOSITES or (now, was) in _OPPOSITES


def _page_says(run: QA, noticed: Dict[str, Tuple[str, str]]) -> None:
    """Turn the facts the page showed about itself into findings.

    These come from reading the page, not from an act someone could repeat,
    so like `_unfillable_boxes` they're numbered in the `F` series.
    """
    for key, (case_id, detail) in noticed.items():
        kind, _, what = key.partition(":")
        if kind == "computed":
            said = (f"the page shows `{what}` where a value should be, "
                    f"\"{detail}\". This usually means a value was used "
                    f"before it was set, or calculated from something that "
                    f"isn't a number")
            asked = "no NaN, undefined or [object Object] on the page"
        elif kind == "aria":
            said = detail
            asked = "the panel a selected tab or open section controls is shown"
        else:
            said = detail
            asked = "labels and radio buttons are linked correctly"
        _finding(run, asked, kind, f"{said}, first seen at {case_id}",
                 subject=f"{asked}: {what}")


def _unfillable_boxes(run: QA, engine: Browser) -> None:
    """Flag a field whose placeholder example fails the field's own `pattern`.

    Someone who types what the example shows can't submit a form that
    requires the field. The check reads the markup instead of typing, because the
    field can sit on a later wizard step that's never on screen. See
    `browser.UNFILLABLE_JS` for why it reads a detached copy and skips
    placeholders that contain a space.
    """
    bad: List[Dict[str, str]] = []
    with contextlib.suppress(Exception):
        with engine.open() as (page, *_):
            bad = browser.unfillable(page)
    for box in bad:
        _finding(run, f"the {box['name']} box accepts its own placeholder "
                      f"example",
                 "unfillable",
                 f"the placeholder shows \"{box['example']}\" as an example, "
                 f"but the pattern on this field, {box['pattern']}, rejects "
                 f"it, so someone who types what the example shows can't "
                 f"submit a form that requires this field")


def _worth_pressing(where: Surface) -> List[Any]:
    """The first few enabled buttons, links and cells, for `_one_look`."""
    return [c for c in where.operable
            if c.kind in ("button", "link", "cell") and c.enabled][:6]


def _waited_out(engine: Browser, surface: Surface) -> bool:
    """Whether the page changes when its controls get more time to respond.

    A case measures soon after it acts, so a Retry that starts a slow load
    looks dead. Before the page-wide "nothing responds" finding is made, the
    page is reopened and watched for seconds instead. The extra page loads
    only happen on a page that's about to be flagged.
    """
    if not _worth_pressing(surface):
        return False
    # A page that fails its own load at random can fail again after Retry,
    # so one look isn't enough.
    for _ in range(SLOW_TRIES):
        if _one_look(engine):
            return True
    return False


def _one_look(engine: Browser) -> bool:
    """Open the page, press its controls, and report whether it changed."""
    with contextlib.suppress(Exception):
        with engine.open() as (page, *_):
            before = browser.signature(page)
            # Measure the reopened page again, because a page that loads
            # differently each time may not have the controls the plan saw,
            # and pressing selectors that no longer exist presses nothing.
            pressable = _worth_pressing(
                from_page(_Shot(browser.elements(page))))
            # Nothing to press means this load differs from the one the plan
            # measured, like a list where the first load showed an error and
            # a Retry button, so it can't confirm the page is dead.
            if not pressable:
                return True
            browser.perform(page, [{"click": c.selector} for c in pressable])
            for _ in range(SLOW_LOOKS):
                page.wait_for_timeout(SLOW_POLL_MS)
                if browser.moved(before, browser.signature(page)):
                    return True
    return False


def _drew(shot: Dict[str, Any]) -> bool:
    """Whether any canvas in this reading holds a picture.

    A picture is anything other than an empty canvas or one flat colour edge
    to edge. A single colour alone doesn't rule a canvas out, because on a
    transparent canvas only the ink is measured, so a black stroke reads as
    one colour.
    """
    # A page that replaces a global the driver evaluates through, such as
    # `eval`, can make a reading come back as something other than a dict.
    # That reading counts as no picture.
    if not isinstance(shot, dict):
        return False
    for row in shot.get("canvas") or []:
        if isinstance(row, list) and len(row) > 7 and row[0] > 0 and row[7] == 0:
            return True
    return False


def _nothing_drawn(run: QA, drew: bool, opened: Opened) -> None:
    """Flag a canvas that never showed a picture during the whole run.

    A canvas of one colour counts as empty, because a WebGL canvas starts
    filled with its clear colour, so counting painted pixels would call it
    full.

    A case only requires a canvas to draw when the page offers nothing else,
    because a chart stays blank until a field beside it is filled. After the
    whole plan has pressed the controls, filled the fields and clicked,
    dragged and typed on the canvas, a canvas that never showed a picture is
    a fault.

    Like `_nothing_responds`, it's skipped when part of the page was
    unreached, because that part might be what draws. It's also skipped when
    any case or finding in the run has already failed.
    """
    if drew or opened.unreached or not opened.surface.canvases:
        return
    acted = [r for r in run.results.values()
             if r.case.acts and r.outcome != UNKNOWN]
    if len(acted) < 2 or any(r.failed for r in run.results.values()):
        return
    _finding(run, "something appears on the canvas", "nothing-drawn",
             f"nothing ever appeared on this canvas. {len(acted)} checks used "
             f"the page, and the canvas stayed one flat colour through all "
             f"of them, so whatever the program draws isn't reaching the "
             f"screen",
             page_wide=True)


def _nothing_responds(run: QA, answered: set, engine: Browser,
                      unreached: Optional[Dict[str, int]] = None) -> None:
    """Flag a page where no control changed anything during the whole run.

    A single control may do nothing visible, so each case only asks that it
    survives being pressed, and a kanban board whose `+ Add` buttons are
    wired to nothing passes every case. This finding catches that at page
    level. Getting it wrong calls a whole page broken, so it needs all of
    these:

    - cases pressed at least two different controls,
    - nothing changed anywhere in the run,
    - `browser.unreached` found nothing the plan missed, because the missed
      part might be the only part that works, like sortable table headers
      when the plan only clicked cells,
    - `_waited_out` saw no change when given more time.
    """
    if unreached:
        return
    acted = [r for r in run.results.values()
             if r.case.acts and r.outcome != UNKNOWN]
    # Count distinct controls, not cases, because one control pressed in two
    # cases is still one control.
    tried = {r.case.control or r.case.id for r in acted}
    if len(tried) < 2 or any(r.case.id in answered for r in acted):
        return
    if run.surface is not None and _waited_out(engine, run.surface):
        return
    _finding(run, "something on the page responds when used",
             "nothing-responds",
             f"nothing on the page changed after any control was used. "
             f"{len(acted)} checks used what the page offers and none of them "
             f"changed it, so the controls don't seem to be connected to "
             f"any code",
             page_wide=True)
