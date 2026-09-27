"""Open a program, work out what it offers, use all of it, and say what broke.

This is the whole of assay from the outside::

    from assay import check
    report = check("./my-app")
    print(report.render())

Nothing here needs a test to have been written, a baseline image, or a
recording. The plan comes from what the page actually renders.
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

#: How long to keep watching a page whose surface never stops changing. This
#: is not how long a page is allowed to take: `browser.settle` returns the
#: moment nothing is arriving, so a fast page costs a few hundred milliseconds
#: whatever this says. It bounds only the pathological case, a feed that
#: grows for ever, and reaching it is reported rather than failed on.
SETTLE_CEILING_MS = 15000

#: How long the page-level rule waits before calling a whole program dead.
#: Long on purpose: a case measures a moment after acting, and something that
#: starts a slow job is still something that answered.
SLOW_LOOKS, SLOW_POLL_MS = 8, 500

#: How many times the page-level guard opens the page before giving up.
#: More than one because a program is allowed to behave differently on each
#: load, and the verdict it is guarding is the most expensive one here.
SLOW_TRIES = 3


@dataclass
class Opened:
    """One page, measured. What `look` hands back."""

    surface: Surface
    #: Uncaught exceptions. **Not the same as a console line.** A page is free
    #: to `console.error` and work, while a throw stops execution, so anything
    #: measured after one is a measurement of a program that stopped.
    crashes: List[str]
    console: List[str]
    failed_requests: List[str]
    title: str = ""
    #: How the page came to rest. `browser.Settled`.
    rest: Any = None
    #: Interactive-looking elements the surface rules did not pick up, by the
    #: reason they looked interactive. Empty means the plan is the whole page.
    unreached: Dict[str, int] = field(default_factory=dict)

    @property
    def blank(self) -> bool:
        """Whether the page rendered nothing a person could see.

        Not *offers no controls*: a page of pure prose offers none and is
        perfectly good. This is no text, no image that loaded, no canvas with
        anything in it: a program whose whole output is an empty document.

        And nothing to work either, which is the guard against the one way
        this could call a working page dead: a grid built from coloured
        `div`s has no text and no canvas, so it renders nothing this can
        see, but its cells are clickable, and a page offering something to
        click is not a blank one whatever it is drawn with.
        """
        return bool(self.rest is not None and self.rest.measured
                    and not self.rest.shown and not self.rest.named)

    @property
    def unmeasurable(self) -> bool:
        """Whether nothing could be read off this page at all.

        Not a verdict about the program: a page that replaces a global the
        driver evaluates through answers every reading with nothing, and what
        that establishes about the program is nothing.
        """
        return bool(self.rest is not None and not self.rest.measured)


class Browser:
    """One browser and one server, held open for a whole run.

    A fresh page per case, not a fresh browser. Every case needs the program
    in its starting state: a paint tool with a cell already filled is a
    different program from one just loaded. A new tab gives you that.
    Launching the engine per case instead cost a browser start and a server
    bind every time: on a 21-case program that is 21 of each, and it turned
    seconds of work into minutes, and a tool meant to run in CI should not
    spend it starting Chromium.
    """

    def __init__(self, folder: Path, entry: str, headless: bool = True) -> None:
        self.folder, self.entry, self.headless = folder, entry, headless
        self._exit = contextlib.ExitStack()
        self._engine: Any = None
        self._play: Any = None
        self._base = ""
        #: How the last page opened came to rest. See `browser.Settled`: the
        #: three facts in it are kept apart because only one of them is a
        #: fault, and the other two are ordinary properties of working pages.
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
        # In this order, and it is not a detail. Handing the teardown to an
        # ExitStack unwinds playwright's own context before the browser it
        # owns has finished closing, and it says so: several lines of
        # `Task was destroyed but it is pending!` and a `TargetClosedError`,
        # printed *after* the results, which reads to anybody running this as
        # a crash rather than a tidy-up.
        with contextlib.suppress(Exception):
            self._engine.close()
        with contextlib.suppress(Exception):
            self._play.stop()
        self._exit.close()

    @contextlib.contextmanager
    def open(self) -> Any:
        """One tab, loaded and settled, with its faults collected."""
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
            # `load` fires when the document and its scripts are fetched, which
            # on anything framework-rendered is before a single control exists.
            self.rest = browser.settle(page, ceiling_ms=SETTLE_CEILING_MS)
            yield page, crashes, console, failed
        finally:
            with contextlib.suppress(Exception):
                page.close()


#: What a page is called, for a path nobody has written yet.
PAGES = (".html", ".htm", ".xhtml")


def aimed(where: str | Path, entry: str) -> Tuple[Path, str]:
    """The folder to serve and the page to open, from whatever was typed.

    **A single file is the obvious thing to point at, and it was the one
    thing this refused.** `assay ./todo.html` answered *"todo.html/index.html
    does not exist"*: a folder named after the page, and a page nobody asked
    for. Measured on a live harness run, where a model handed a one-file
    program typed exactly that, got exactly that, and went on to invent an
    answer rather than ask again.

    Both facts are real and a file path states both at once. The folder is
    what gets served, because a page's siblings are part of it; which of
    those to open is separate, and defaults to `index.html` only because
    something has to.

    The suffix decides it rather than the file being there, which is the
    test `unbuilt` already makes. A path ending `.html` is a page whether or
    not anybody wrote it, and *"todo.html does not exist"* is the answer to
    the question that was asked. A directory is never split, whatever it is
    called.
    """
    aim = Path(where).expanduser()
    if aim.is_dir():
        return aim, entry
    if aim.is_file() or aim.suffix.lower() in PAGES:
        return aim.parent, aim.name
    return aim, entry


def look(folder: str | Path, entry: str = "index.html") -> Opened:
    """What this program offers, measured from the rendered page."""
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
    """What `surface.from_page` reads. Kept tiny on purpose."""

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
    """Whether one case came out right, and the numbers either way.

    The rules are narrow on purpose, and each one is narrow because a wider
    version of it called a working program broken.
    """
    quiet = bool(case.expect.get("quiet"))
    bad: List[str] = []
    rules: List[str] = []

    def flag(rule: str, said: str) -> None:
        rules.append(rule)
        bad.append(said)

    # **Nothing could be read off this page, so nothing is settled.** A page
    # that replaces a global the driver evaluates through (`function eval()`
    # is the one that has actually turned up) answers every reading with
    # nothing. That is the instrument being out, not the program being
    # broken, and the two must never come out the same: a check that could
    # not run reading like one that failed is the fault this tool is for.
    if unmeasurable:
        return Result(case=case, outcome=UNKNOWN,
                      detail="assay could not read this page, because the "
                             "page replaces a built-in function that assay "
                             "relies on (such as `eval` or `Function`). This "
                             "says nothing about whether the page works",
                      evidence="")

    # **A page that rendered nothing is not a page that works.** It is the one
    # thing the derived plan cannot otherwise report: an app that mounts
    # nothing offers no controls, so the plan is a single case that asserts
    # only that nothing threw, and an empty document throws nothing. That
    # came back `1 case, 1 passed, exit 0` about a React app whose component
    # returned null for ever. No text, no image, no paint: whatever else is
    # true of the program, what it renders is a blank page.
    # …but only once there was a chance for something to appear. A freehand
    # drawing tool is an empty canvas and nothing else until somebody draws
    # on it, and at load it is indistinguishable from a dead game that draws
    # nothing ever. What separates them is whether anything answers: so this
    # fails a case that *acted* and left the page still empty, or a page that
    # offers nothing to act on at all. A blank page with a canvas on it gets
    # to be judged by what the canvas does, and by a case that actually
    # asserts something, never by a coverage case, which promises only that
    # nothing threw. Clicking a blank canvas once and it staying blank is
    # the coverage case doing exactly what it says.
    if blank and (nothing_to_try or (case.acts and not quiet)):
        flag("blank", "the page shows nothing at all (no text, no images and "
                      "nothing drawn), so there is nothing to test")

    # **A page that threw is not the program the case is about.** Everything
    # after an uncaught exception did not happen.
    if crashes:
        flag("threw", f"the page threw an error and stopped running: "
                      f"{crashes[0]}")

    # An act the page refused fails a case only when nothing could be done.
    # A canvas behind a "press Space to start" overlay cannot be clicked, and
    # that is the program working, and a `quiet` case never fails on one at
    # all, because `quiet` asserts only that nothing threw.
    if could_not and not quiet and len(could_not) >= len(case.acts or [None]):
        flag("could-not", "could not " + "; nor ".join(could_not[:3]))

    if case.expect.get("painted") and browser.unpainted(after):
        flag("unpainted", f"{browser.unpainted(after)} canvas(es) still show "
                          f"nothing after every step of this check")

    # **Saved, and gone after a reload.** The page wrote these into its own
    # storage and was showing them, so it has said they are kept.
    if lost:
        flag("forgot-on-reload",
             f"{' and '.join(repr(one) for one in lost[:2])} "
             f"{'was' if len(lost) == 1 else 'were'} saved in browser storage "
             f"by the page, but {'is' if len(lost) == 1 else 'are'} gone after "
             f"reloading it")

    want = str(case.expect.get("want") or "")
    if want and want.lower() not in (text or "").lower():
        flag("missing-text", f"the page does not contain {want!r}")

    acted = bool(case.acts)
    shifted = browser.moved(before, after)
    # **A case that brings its own rule is not also judged by the floor.**
    # The floor asks *did anything change at all*, which is the right
    # question for a case that names one act and the wrong one for a case
    # whose whole point is how two acts compare with each other, and it
    # fires first, so its complaint is what gets reported. That is how the
    # off-by-one case came to fail every button on a working painter with
    # `the first press: changed the page` printed in its own evidence.
    own_rule = any(case.expect.get(k) for k in ("again", "same_each"))

    # **A program that ran to a stop on its own reached a state it chose,
    # and what it does afterwards is not evidence it was never wired.** A
    # snake plays itself, hits a wall, and sits there ignoring the keyboard,
    # which is the game working exactly as its objective asks. Pressing keys
    # at a finished program and reporting that nothing on the page is wired
    # describes the tool's timing, not the program.
    #
    # **Unless the page said what to press.** That is the whole of the
    # difference, and it is readable: one snake puts `Game Over! Press Space
    # to restart.` on the screen and ignores Space, which is a contract it
    # wrote itself and broke, and the other says nothing and owes nothing.
    # From outside they are otherwise the same page.
    promised = browser.told_to_press(text)
    asked = browser.was_pressed(promised, case.acts)

    if (acted and not quiet and not case.expect.get("unchanged")
            and not own_rule and not stirred
            and browser.aimed_at_canvas(case.acts)
            and browser.canvas_still(before, after)):
        flag("canvas-unchanged",
             "the canvas this check clicked did not change, even if other "
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

    # **One row fewer, and the one you pressed is still there.** A bookmark
    # manager splicing at the wrong index removes the row beneath the button
    # instead of the row holding it, and the last row can never be removed
    # at all. Every count is right, the page changes exactly as much as it
    # should, and the wrong thing went. It takes two rows on screen to see
    # it, which is why the plan has to fill the page in first.
    was_row, now_row = rows
    # **Two rows that read the same cannot say which of them went.** A list
    # of amounts where every row shows the same figure leaves a survivor
    # indistinguishable from the one that was removed, and reading that as
    # the wrong row going is a working page reported for arithmetic.
    alike = (was_row or {}).get("all") or []
    told_apart = alike.count((was_row or {}).get("text")) == 1
    if (was_row and now_row and was_row.get("text") and told_apart
            and int(now_row.get("many") or 0) < int(was_row.get("many") or 0)
            and was_row["text"] in (now_row.get("all") or [])):
        flag("wrong-row", f"this removed a row, but not the one it belongs "
                          f"to: {was_row['text'][:60]!r} is still there")


    # **A surface that took the first stroke has to take the second.** The
    # first stroke is the setup, so `before` already has its marks in it and
    # `answered_setup` says whether it drew at all.
    #
    # A canvas that ignored the first stroke is not a drawing surface and is
    # asked nothing. A chart exempts itself by not answering, which is why
    # this needs no policy about what kind of canvas it is looking at. The
    # program establishes its own baseline, exactly as the settle rule does.
    # **A control that answers only its second press has lost one.** Both
    # presses are the same act; `answered_once` says what the first one did
    # and `before`/`after` bracket the second. Nothing here reads the words
    # on the control: a page where the first press does nothing and the
    # second does something is incoherent whatever the button is called.
    if case.expect.get("same_each"):
        # **Asked of the square itself, where the square is what was
        # clicked.** A scheduler whose booked styling was inverted leaves
        # the cell plain on the first click and looking booked on the
        # second, and the page moved both times because a summary line
        # followed. Asked of the page, both presses answered and nothing was
        # wrong; asked of the cell, the first press did nothing to the thing
        # it was aimed at.
        #
        # A gallery thumbnail that opens a lightbox is unchanged by *both*
        # presses and is right to be. What makes this a fault is the
        # disagreement between the two, not the silence of either.
        was, now, back = (list(itself) + [None, None, None])[:3]
        if case.expect.get("itself") and was is not None and now is not None:
            # **The square has to answer the second press, not only the
            # page.** A key on an on-screen keyboard never changes itself:
            # each press types a letter on the board. Reading the page
            # moving as the square answering called every key one behind.
            if was == now and back is not None and back != now \
                    and shifted is True:
                flag("one-behind-cell",
                     "clicking this twice: the first click did not change it "
                     "and the second did, so it reacts one press late")
            # **It went back and the page did not.** A tag that switches
            # itself off is saying the filter it switched on is off again,
            # and a list still filtered contradicts it. Both halves are the
            # page's own: the control's own appearance, and whether the page
            # is where it started.
            #
            # It has to have changed in the first place. A button that never
            # alters itself is the ordinary case, and pressing one twice is
            # allowed to leave the page twice as far along.
            #
            # **And the second press has to have done nothing but put the
            # control back.** A tree folder that collapses the folders inside
            # it when it closes reopens with them still closed, which is the
            # page choosing a tidy state, and it says so by redrawing its
            # children and its row count on the second press. A tag whose
            # list stays filtered does nothing on the second press except
            # unlight itself. `elsewhere` is that second press, measured
            # outside the control and the wrappers around it.
            elif (was != now and back == was and page_back is True
                  and elsewhere is False):
                flag("went-back",
                     "clicking this twice switched it back off, but the rest "
                     "of the page did not change back, so what the first "
                     "click did is still in effect")
        elif answered_once is False and shifted is True:
            flag("one-behind",
                 "pressing this twice from the same starting point: the first "
                 "press changed nothing and the second did, so it reacts one "
                 "press late")
        return Result(case=case, outcome=FAILED if bad else PASSED,
                      detail="; ".join(bad)[:400], rules=rules,
                      evidence=(f"the first press: "
                                f"{'changed the page' if answered_once else 'did nothing'}"
                                f"; the second: {browser.changed(before, after)}")[:400])

    if case.expect.get("again") and answered_setup:
        if shifted is False:
            flag("second-stroke",
                 "the first line drawn on this canvas appeared, but a second "
                 "line drawn elsewhere did not, so the canvas stopped "
                 "accepting drawing")

    # **A control the program switched off is the program answering.**
    # `was_off` is an act the driver could not perform because the page had
    # `disabled` on the target, and it was collected, printed in the evidence
    # and then ignored by the verdict. A quantity box declaring `max="10"`
    # was filled with 25, the program clamped it to 10 and disabled `+`,
    # exactly as it should, and assay pressed the disabled `+`, saw nothing
    # move and reported that nothing on the page is wired. The page had
    # stated the reason in the plainest way a page can.
    #
    # It costs a miss where a control is disabled and should not be, which
    # is the cheap error: `disabled` is the program saying *not now*, and
    # taking its word is how a limit gets to be a limit.
    observed = browser.changed(before, after)
    if was_off:
        observed += ("; " if observed else "") + (
            f"{was_off[0]}: the program has that control disabled")
    if could_not and not bad:
        observed += ("; " if observed else "") + (
            "could not " + could_not[0] + ", and the rest of the case went ahead")

    return Result(case=case, outcome=FAILED if bad else PASSED,
                  detail="; ".join(bad)[:400], evidence=observed[:400],
                  rules=rules)


def _text(page: Any) -> str:
    """The words on the page, or nothing if they could not be read."""
    with contextlib.suppress(Exception):
        return page.inner_text("body")[:3000]
    return ""


def _shoot(page: Any, into: Optional[Path], name: str) -> str:
    """A picture of the page, or nothing when none are being kept.

    Full page rather than viewport: a report whose screenshot stops at 800px
    cuts off the thing that failed about as often as not.
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
    """Which pictures are worth keeping.

    Two identical screenshots of a page that did not move are not evidence
    twice over, they are the same evidence and a reader scrolling past sixteen
    of them stops looking. When the bytes match, one is kept and the report
    says the page is unchanged, which is more information than the pair, not
    less.
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
    """The acts that fill a widget and submit it, if the plan has any.

    Taken from the plan rather than invented, because working out what to
    type into which box and which button sends it is exactly what the plan
    already did. The shortest one: a widget with two fields is filled
    together, and the case naming the first field carries the same acts as
    the case naming the second.
    """
    submits = [c for c in cases
               if c.expect.get("changes") and c.acts
               and any("fill" in act for act in c.acts)
               and any("click" in act for act in c.acts)]
    if not submits:
        return []
    return list(min(submits, key=lambda c: len(c.acts)).acts)


#: A second value for a field, so the two rows a page is filled with are
#: not the same row twice.
_SECOND = {"Sample item": "Another item",
           "someone@example.com": "nobody@example.com",
           "https://example.com/page": "https://example.com/other",
           "2026-03-14": "2026-03-21", "09:30": "10:45",
           "2026-03-14T09:30": "2026-03-21T10:45", "2026-03": "2026-04",
           "2026-W11": "2026-W12", "555-0100": "555-0199", "3:30": "4:15"}


def _twice(seed: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    """The filling, done twice, with something different the second time.

    **Two rows that say the same thing cannot show which of them went.** A
    bookmark manager removing the row beneath the button instead of the row
    holding it leaves a list that reads exactly as it would have if the
    right one had gone, when both rows carry the same title.
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
    """Cases for the controls a page only grows once it is holding something.

    **A to-do list at load is a box and a button.** The checkbox, the Delete
    beside each row and the count of what is left do not exist until a row
    does, so a plan derived from the page as it arrives cannot reach the
    things most likely to be wrong. Half the programs in the planted set are
    this shape.

    The page is filled in and submitted twice, so the list holds more than
    one thing: a Delete that removes the wrong row cannot show that with one
    row on screen. Then the surface is measured again and the ordinary
    planner is asked for cases about it, and every case that reaches a
    control which was not there before is kept, with the filling in front of
    it so it can be carried out from a page that has just loaded.
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
    """Measure, plan, carry it all out, and report. The whole thing.

    `shots` is a folder to keep screenshots in, one before and one after each
    case. Without it nothing is written and the run is a little faster, which
    is what you want from a CI check that only cares about the exit code.
    """
    # The same reading the command line gives a path: a file is the page,
    # a folder holds one. Both entry points agree, so `check("./todo.html")`
    # and `assay ./todo.html` open the same thing.
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
        #: Every control the page offered, as loaded and as it grew, by
        #: selector. What the links are allowed to call one kind of thing.
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
                    # **A page that saves what it was given has said it
                    # will be there next time.** Writing the entries into
                    # its own storage is the page's promise, and a reload
                    # is the only way to hold it to it. Asked only of what
                    # was both saved and showing before the reload.
                    cases.append(Case(
                        id="", what="save two, reload, and they are still "
                                    "there",
                        acts=_twice(seed) + [{"reload": "page"}],
                        expect={"survives": kept, "quiet": True},
                        origin="seeded"))
        for n, case in enumerate(cases, 1):
            case.id = f"C{n:03d}"
        # Nothing to press, type into or draw on. A page like that has only
        # one thing to say for itself, so an empty one is empty for good.
        nothing_to_try = not (opened.surface.operable
                              or opened.surface.canvases)

        #: Which cases saw the page move. `Result.evidence` cannot answer
        #: this, because it is a description, and "the visible text is unchanged"
        #: is a perfectly full string.
        answered: set = set()
        #: Whether any measurement in any case ever saw more than one colour
        #: in a canvas. A run-level fact, because no single case can hold it:
        #: a chart is blank until something is typed into the field beside it,
        #: and the case that fills that field is not the one that looks.
        drew: List[bool] = []
        #: What the page said about itself, against the first case that saw
        #: it. Kept once each: a label pointing at nothing is the same fault
        #: whether one case noticed it or fifteen did, and reporting it
        #: fifteen times buries everything else.
        noticed: Dict[str, Tuple[str, str]] = {}
        #: Per control, whether pressing it was ever seen to change the page.
        #: Absent means it was never pressed, which is a third thing and not
        #: the same as pressed and silent.
        worked: Dict[str, bool] = {}
        #: Whether this page moves on its own, measured once and kept. A
        #: clock that changes once a second needs longer than a case can
        #: spare to observe, and the answer is a property of the page rather
        #: than of any one case.
        ticking: List[Optional[bool]] = [None]
        #: Every reading of (how many things are on show, what each displayed
        #: number said). One per case, because each case leaves the page in a
        #: different state, and it takes several states to tell a number that
        #: is counting the list from one that happens to match it once.
        counts: List[Dict[str, Any]] = []
        #: The page either side of each case, so a number can be watched
        #: following the list up and failing to follow it down.
        swings: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        #: Per case that typed something and submitted it: what was typed,
        #: and what the page held afterwards. Judged at the end, because
        #: which of its classes are a *list* is only knowable once the page
        #: has been seen at more than one size.
        entries: List[Tuple[str, List[str], Dict[str, Any]]] = []
        #: What every tab logged as an error and every request that failed,
        #: kept as information. A page may log an error and work, so none of
        #: it decides anything.
        heard: List[Tuple[List[str], List[str]]] = [
            (opened.console, opened.failed_requests)]
        #: Each case's crashes, and how many had already happened when the
        #: page finished loading and before any act.
        crashed: Dict[str, Tuple[List[str], int]] = {}

        def carry_out(case: Case) -> Result:
            with engine.open() as (page, crashes, console, failed):
                heard.append((console, failed))
                crashed[case.id] = (crashes, len(crashes))
                before = browser.signature(page)
                shot_before = _shoot(page, shots, f"{case.id}-before")
                # **A case asserts about its last act, not about its own
                # typing.** Filling a field changes the page, because the field
                # now holds what was typed, so a case that types and then
                # presses a dead button was satisfied by its own keystrokes,
                # and a todo list whose Add does nothing passed. The setup
                # runs first and is measured out of the way; what has to
                # answer for itself is the act the case is named for.
                # ...but only where the setup is *typing*. A canvas case is
                # click, drag and a run of keys, and the whole sequence is
                # the point: measuring just its last act put the keyboard's
                # effect into the *before* picture and failed a canvas that
                # answers the keyboard. Filling is setup; pressing is not.
                # The same split serves the second-stroke case, and for the
                # same reason: what has to answer is the stroke the case is
                # named for, so the first stroke's marks belong in the
                # *before* picture or the case is satisfied by them.
                fills_first = (len(case.acts) > 1
                               and (all("fill" in a or "pick" in a
                                        or "choose" in a
                                        for a in case.acts[:-1])
                                    or case.expect.get("again")))
                # The second-stroke case is one stroke of setup and every
                # trial after it, not everything-but-the-last: the trials are
                # alternatives, and burying all but one of them in the setup
                # would make the extra places change nothing.
                setup, final = (
                    (case.acts[:1], case.acts[1:])
                    if case.expect.get("again") or case.expect.get("second")
                    else (case.acts[:-1], case.acts[-1:]) if fills_first
                    else ([], case.acts))
                # **Let an animating canvas come to rest before acting**, so
                # that whatever moves afterwards moved because of the acts.
                # Without this a game that plays itself changes during the
                # case whatever is pressed, and one that had already died
                # passed on the strength of its own last frames.
                # The second-stroke case needs this every bit as much as
                # the `changes` case does, and for one reason: on a canvas
                # that moves by itself, *the first stroke drew* is a
                # sentence about the animation. Two working snakes were
                # called painters that had forgotten how to draw.
                wants_rest = (case.expect.get("changes")
                              or case.expect.get("again"))
                rested = (browser.settle_canvas(page)
                          if wants_rest and (before.get("canvas") or [])
                          else browser.Rested(False, False))
                itself_before = (browser.itself(page, case.control)
                                 if case.expect.get("itself") else None)
                was_quiet = rested.quiet
                # Moving when the watch began and still by the end: the
                # program ran and stopped on its own terms.
                self_stopped = rested.quiet and rested.moved
                if was_quiet:
                    before = browser.signature(page)
                if case.expect.get("again") and not was_quiet:
                    # Still moving, so nothing here is attributable to a
                    # stroke. A game is not a drawing surface, and this case
                    # has no question to ask of one.
                    return Result(case=case, outcome=PASSED, detail="",
                                  evidence="this canvas is still moving on "
                                           "its own, so a stroke cannot be "
                                           "told from the animation")

                # **The off-by-one case is measured between its two
                # presses**, because that is the whole question: a control
                # answering only the second press is what has to be visible,
                # and a before-and-after across both cannot see it.
                if case.expect.get("same_each"):
                    setup_acts = case.acts[:-2]
                    if (len(setup_acts) == 2
                            and all("drag" in a for a in setup_acts)):
                        # **Two strokes, and the second has to have drawn.**
                        # The question is whether a control takes back one
                        # step per press, and it rests on there being two
                        # steps. A painter that can only draw in one corner
                        # leaves the second stroke without a mark, and its
                        # correct Undo then spends its first press on that
                        # empty step and looked one behind. A drawing
                        # surface that ignored the stroke is the second-
                        # stroke case's business, not this one's.
                        cn, wo = browser.perform(page, setup_acts[:1])
                        one_stroke = browser.signature(page)
                        cn2, wo2 = browser.perform(page, setup_acts[1:])
                        could_not, was_off = cn + cn2, wo + wo2
                        two_strokes = browser.signature(page)
                        if browser.canvas_still(one_stroke, two_strokes):
                            if browser.moved(before, one_stroke):
                                answered.add(case.id)
                            drew.append(_drew(one_stroke))
                            # Judged for everything but the one question it
                            # cannot ask: a page that threw is still a page
                            # that threw.
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
                    # **Both rules about a square compare the page either
                    # side of a press, and a page that moves on its own
                    # differs either side of anything.** A world clock ticks,
                    # so a toggle that switched itself back looked like one
                    # whose effect had stuck. `settle_canvas` cannot answer
                    # this: it is only asked where there is a canvas, and a
                    # grid has none. So the page is watched doing nothing for
                    # a moment, which is the whole question.
                    watched = bool(case.expect.get("itself"))
                    if watched and ticking[0] is None:
                        # Long enough to see a clock tick, which is the
                        # slowest thing that counts as moving on its own.
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
                    # The element either side of the *first* press, against
                    # a page compared either side of the second: the
                    # question is whether the square sat out the press it
                    # was given.
                    result = judge(
                        case, after_one, after, crashes, could_not, was_off,
                        _text(page), answered_once=answered_once,
                        # **Neither of these can be asked of a page that
                        # moves on its own.** A world clock ticks, so it is
                        # never where it started and a toggle that switched
                        # itself back looks like one whose effect stuck.
                        # Withholding the measurement stands both rules
                        # down at once, which is what an unanswerable
                        # question deserves.
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
                # **A page that answered and went back is a page that
                # answered.** `before` and `after` bracket the whole case, so
                # a sequence returning to where it started reads exactly like
                # one that was ignored. A palette answered a click on a shape
                # by outlining it and answered the next click by putting the
                # outline away, 18540 painted pixels to 19276 and back to
                # 18540, and was reported as a canvas that does not respond.
                # Only a sequence can do this, so a lone act pays nothing.
                was_counted = browser.counted(page)
                row_before = None
                stirred = False
                if len(final) > 1:
                    could_not_more, was_off_more = [], []
                    # **Which of the two presses answered.** A sequence is
                    # judged as one measurement, which is right: what it
                    # asks is whether the page responded to the pair. But a
                    # control only ever gets its turn inside a pair when it
                    # needs the other one to have gone first, and Previous
                    # on a freshly loaded page is exactly that. Attributed
                    # here because the loop is already taking a signature
                    # between the steps.
                    seen = before
                    for at, step in enumerate(final):
                        # **The row has to be read after the page has been
                        # filled in and before the button is pressed.** These
                        # cases carry their own setup: the whole point is a
                        # control that does not exist until the page is
                        # holding something, so on a freshly loaded page
                        # there is no row to be in.
                        if at == len(final) - 1:
                            # **The swing is about the last act, not the
                            # whole case.** A seeded case fills the page in
                            # and then presses Delete, so measured end to
                            # end the list has *grown* and the removal is
                            # invisible inside it.
                            was_counted = browser.counted(page)
                            # **Only where the case presses one thing
                            # once.** A pair of clicks on two cells removes
                            # a row and then presses a selector that now
                            # means a different row, and reading that as the
                            # wrong row going flagged a working basket.
                            if case.control and case.origin == "seeded":
                                row_before = browser.row_of(page,
                                                            case.control)
                            # **The list with two rows in it, before the
                            # case's own press.** One row cannot show a row
                            # holding the wrong figure when that figure is a
                            # running total: with one row the total is the
                            # amount. Each submission is asked about on its
                            # own, so a second one the page refused is not
                            # read as the first one's words going missing.
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
                # **A canvas that paints on a timer may not have painted
                # yet.** `settle` watches the set of controls, and a later
                # draw does not change it, so a game whose first frame lands
                # a moment after the page is ready can be read as an empty
                # canvas. That failed a working snake, intermittently, which
                # is the worst way for anything here to be wrong. Waiting is
                # only allowed to turn *empty* into *drawn*: it cannot
                # manufacture a pass for a canvas that stays blank.
                if case.expect.get("painted") and browser.unpainted(after):
                    page.wait_for_timeout(1200)
                    after = browser.signature(page)
                # **A field can be submitted by pressing Enter**, and some
                # pages have no submit button at all: one todo list adds a
                # task on `keydown` and its only button is a `Clear
                # completed` sitting in the same container, which takes
                # nothing from the field and is right not to. The case means
                # *submitting this does something*, so before failing it,
                # try the other way of submitting. This can only turn a
                # failure into a pass. It never manufactures one.
                if (case.expect.get("changes") and setup
                        and browser.moved(before, after) is False):
                    with contextlib.suppress(Exception):
                        typed = setup[-1].get("fill", "").split("=")[0]
                        page.focus(typed)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(500)
                        after = browser.signature(page)
                if was_quiet and browser.moved(before, after) is False:
                    # Quiet before, acted on, still quiet: nothing answered.
                    # Give it the same grace a first paint gets, in case the
                    # response is on a timer.
                    page.wait_for_timeout(900)
                    after = browser.signature(page)
                itself_after = (browser.itself(page, case.control)
                                if case.expect.get("itself") else None)
                lost = (browser.missing_from(page, case.expect["survives"])
                        if case.expect.get("survives") else [])
                shot_after = _shoot(page, shots, f"{case.id}-after")
                text = _text(page)
                # Read now, not at load: a canvas is meant to be empty until
                # something is done to it, so what settles whether this page
                # shows nothing is what it shows *after* the case.
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
        # **A page that never came to rest is not a page that answers
        # nothing.** This finding is about the whole program, so it has to
        # be sure the whole program arrived, and `settle` giving up at its
        # ceiling means exactly that it could not tell. One page here loads
        # its list after a delay: on a quiet machine it settles and is
        # tested properly, and on a busy one it was still arriving, offered
        # one control instead of two, and was called dead. A verdict must
        # not depend on how loaded the machine is.
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
    """Record something the whole run established, under an id of its own.

    These are not acts anybody could repeat, so they are numbered apart from
    the plan: `F` for a fact the page showed while it was used, and `C000`
    for the one verdict about the page as a whole. The id is the first one
    free, so two findings can never land on the same slot and overwrite
    each other.
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


#: A value a field could hold and arithmetic could use.
_A_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def _typed_junk(case: Case) -> bool:
    """Did this case put something in a box that is not a number?

    **The page is not at fault for arithmetic on what assay typed into it.**
    A temperature converter is given `Sample item`, multiplies it by nine
    fifths, and correctly shows `NaN` in the other box. Reporting that blames
    a working program for answering the question it was asked, and every
    converter and calculator would meet it.

    Empty counts as a number here, because a field cleared is a field
    holding nothing rather than holding rubbish.
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

    Measured after every case rather than once at load, because a page is
    allowed to be fine when it arrives and wrong once it is used.  Keeping
    the first case that showed it is what makes the finding actionable,
    since that case is the way to see it again.
    """
    if not _typed_junk(case):
        for bad in seen.get("computed") or []:
            noticed.setdefault(f"computed:{bad.get('token')}",
                               (case.id, str(bad.get("around") or "")))
    # Markup is markup whatever was typed at it.
    for why in seen.get("wiring") or []:
        noticed.setdefault(f"wiring:{why}", (case.id, why))
    for why in seen.get("aria") or []:
        noticed.setdefault(f"aria:{why}", (case.id, why))


#: Words that mean the opposite of each other, as a page labels its
#: controls. Deliberately short: each pair has to be a genuine reversal, so
#: that a page offering both is a page claiming one undoes the other. `on`
#: and `off` are not here because one button is routinely labelled with the
#: state it will move to rather than the state it is in.
_OPPOSITES = (
    ("next", "previous"), ("next", "prev"), ("forward", "back"),
    ("forward", "backward"), ("undo", "redo"), ("up", "down"),
    ("increase", "decrease"), ("more", "less"), ("plus", "minus"),
    ("add", "remove"), ("add", "delete"), ("expand", "collapse"),
)

#: What survives from a label when the emoji and punctuation are taken off.
_WORDS = re.compile(r"[a-z]+")


#: What is safe to look for afterwards. The long and awkward probes are
#: deliberately absent: a page is allowed to trim three hundred characters or
#: escape a quotation, and neither is a fault.
_PLAIN = re.compile(r"^[\w .@:/-]{2,40}$")

#: A date or a time as a box holds it. **A page is free to show one however
#: it likes**: `2026-03-14` in the box is `14 March` in the row, and looking
#: for the box's own spelling in the row would call a correct list broken.
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
    """Which classes are a list: the ones whose count varies across the run.

    Waiting for two of something on screen at once misses the commonest
    shape there is, because a page that goes from holding nothing to holding
    one thing has shown you a list.
    """
    every = {name for seen in counts for name in (seen.get("classes") or {})}
    return {name for name in every
            if len({int((seen.get("classes") or {}).get(name) or 0)
                    for seen in counts}) > 1}


def _never_shown(run: QA, counts: List[Dict[str, Any]],
                 entries: List[Tuple[str, List[str], Dict[str, Any]]]) -> None:
    """Something typed in, accepted into a list, and not in the row it made.

    **Accepted is not the same as owed on screen.** A sign-up form takes an
    address and a password, says *Account created*, and shows neither, which
    is correct and in the password's case required. The first version of
    this asked only whether the page had grown, and reported exactly that
    form. A row in a list is different: it exists to show what went into it,
    and a bookmark whose Open link carries the title instead of the address
    has lost the address entirely.

    So the question is asked of the list rather than of the page, and only
    of a page that has one, which is why it waits until the end: what counts
    as a list is settled by watching it change size.
    """
    lists = _lists_in(counts)
    # **A table's rows carry no class**, so they never show up as a list
    # above, and an expense table is exactly that shape. Rows whose count
    # changed across the run are a list by the same test.
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
            # All of it missing is a row that carries none of what was
            # entered, which is the shape of a list showing something else
            # entirely and not of one field going astray. Left alone until
            # there is a program that proves it a fault.
            continue
        _finding(run, "values typed into a list show up in the new row",
                 "never-shown",
                 f"{', '.join(repr(one) for one in gone[:2])} was typed in "
                 f"and accepted, but the new row in the list does not show "
                 f"it; first seen at {case_id}",
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
    """One of a pair that reverses the other works, and the other never does.

    **A lone button is allowed to do nothing visible and this does not take
    that back.** A palette swatch sets the current colour and shows no
    selection border, and demanding an answer from it called nine of
    twenty-one cases on a working paint tool broken. What a page cannot
    explain is offering Next and Previous, answering one of them every time
    it is pressed, and never once answering the other.

    The reversal is the whole of it, and it is read from the page's own
    labels rather than assumed: two controls whose words differ by exactly
    one, and that one word a genuine opposite. A flashcard deck whose
    Previous is wired to a condition that can never be true meets it, and so
    does a history with a dead Redo.

    Order is why both orders are planned. Previous on a freshly loaded deck
    does nothing and is right to, so the press that counts is the one inside
    `Next, then Previous`, and that is where the attribution comes from.
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
                     f"{a.label} changed the page every time it was pressed, "
                     f"but {b.label} never did, even right after {a.label}. "
                     f"As a pair, {b.label} should reverse what {a.label} "
                     f"does")
            return


def _how_many(seen: Dict[str, Any], lists: Sequence[str]) -> int:
    """How many things were on show in one reading.

    The largest single repeated thing rather than the sum of them, because a
    row holds its own parts: a bookmark carries a title and a link that
    repeat exactly as often as the bookmark does, and adding those together
    counts one row three times.
    """
    classes = seen.get("classes") or {}
    return max([int(seen.get("rows") or 0)]
               + [int(classes.get(name) or 0) for name in lists])


def _counts_wrong(run: QA, counts: List[Dict[str, Any]]) -> None:
    """A number counting the list, that disagrees with the list.

    **The page says which number is about the list, by moving them
    together.** A bookmark manager whose counter reads one fewer than the
    rows beneath it changes that counter by one every time a row arrives, so
    it plainly is the count; it is simply always wrong by the same amount.
    Nothing here decides what a number is for. It is read off how the number
    behaves across the whole run, and a number that does not move with the
    list is never looked at again.

    **And being off by a constant is not enough on its own.** A basket
    charging a flat fee moves in step with its contents and is right at every
    step. What cannot be right is a count that is not zero when there is
    nothing to count, and that is the whole of the test: the page showed an
    empty list and a number about that list saying there was something.

    Whole numbers only. A decimal point is a measurement rather than a
    count, and money is the exact thing a count must not be confused with.
    """
    if len(counts) < 3:
        return
    # **A list is a thing whose count varies.** Waiting for two of it on
    # screen at once misses the commonest shape there is: a page that goes
    # from holding nothing to holding one thing has shown you a list, and a
    # run that never fills it twice never learns that.
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
                 f"the list is empty. It is {off:+d} off at every size",
                 evidence="; ".join(f"{size} shown, it says {said}"
                                    for size, said in sorted(pairs))[:300])
        return


def _said(seen: Dict[str, Any]) -> Dict[str, str]:
    """What each displayed number said, as it was written."""
    return {str(n.get("at")): str(n.get("said"))
            for n in seen.get("numbers") or []}


def _follows_one_way(run: QA, counts: List[Dict[str, Any]],
                     swings: List[Tuple[Dict[str, Any], Dict[str, Any]]]
                     ) -> None:
    """A number that follows the list when it grows and not when it shrinks.

    **An expense tracker that forgets to re-total on delete.** Adding moves
    the total every time, so the page has said plainly that the total is
    about the list; removing a row leaves it standing at a figure for money
    that is no longer owed. Nothing here does the arithmetic, and it does
    not need to: the question is only whether the number moved, and the page
    answered it one way a moment earlier.

    Money is deliberately allowed here where the counting rule refuses it. A
    running total is the commonest number that should follow a list, and
    following is a weaker claim than equalling.

    Both directions have to have been seen, and the growing side has to be
    unanimous. A number that sometimes moves and sometimes does not is a
    number doing something else.
    """
    # No guard on there being a class that repeats: a table's rows are
    # `<tr>` and carry no class at all, and an expense tracker is exactly
    # that shape. What settles whether there is a list here is that the
    # count moved.
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
    """Whether two labels differ by exactly one word, and that word a
    reversal."""
    a, b = set(_WORDS.findall(one.lower())), set(_WORDS.findall(other.lower()))
    left, right = a - b, b - a
    if len(left) != 1 or len(right) != 1:
        return False
    was, now = left.pop(), right.pop()
    return (was, now) in _OPPOSITES or (now, was) in _OPPOSITES


def _page_says(run: QA, noticed: Dict[str, Tuple[str, str]]) -> None:
    """Turn what the page said about itself into findings.

    Read rather than driven, like `_unfillable_boxes` beside it, and
    numbered in the same `F` series for the same reason: none of these is an
    act somebody could repeat, they are things that were true while the page
    was being used.
    """
    for key, (case_id, detail) in noticed.items():
        kind, _, what = key.partition(":")
        if kind == "computed":
            said = (f"the page shows `{what}` where a value should be: "
                    f"\"{detail}\". This usually means a value was used "
                    f"before it was set, or calculated from something that "
                    f"is not a number")
            asked = "no NaN, undefined or [object Object] on the page"
        elif kind == "aria":
            said = detail
            asked = "the panel a selected tab or open section controls is shown"
        else:
            said = detail
            asked = "labels and radio buttons are linked correctly"
        _finding(run, asked, kind, f"{said}; first seen at {case_id}",
                 subject=f"{asked}: {what}")


def _unfillable_boxes(run: QA, engine: Browser) -> None:
    """A box whose own example fails its own rule is a form nobody can finish.

    The one finding here that is read rather than driven, and it has to be:
    the field that prompted it sits on a later step of a wizard, so it is
    never on screen to be typed into, and every step before it advances
    perfectly well. Driving the page can only reach what the page is
    currently showing.

    What makes it a fact rather than an opinion is that the two things
    disagreeing both belong to the page: its own `pattern` and its own
    worked example. See `browser.UNFILLABLE_JS` for why it is asked of a
    detached copy and why a placeholder with a space in it is left alone.
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
                 f"it, so nothing typed can pass and a form that requires it "
                 f"cannot be completed")


def _worth_pressing(where: Surface) -> List[Any]:
    """What the page-wide guard presses: the first few things to click."""
    return [c for c in where.operable
            if c.kind in ("button", "link", "cell") and c.enabled][:6]


def _waited_out(engine: Browser, surface: Surface) -> bool:
    """Press what the page offers and wait properly. Did anything happen?

    **The most expensive verdict here is the one that gets the most
    patience.** Every case measures a moment after it acts, which is right
    for a button that answers immediately and wrong for one that starts
    something slow: a page whose Retry begins a two-second load looks inert
    in the four hundred milliseconds a case allows it, and the page-level
    rule then calls the whole program dead.

    So before that rule is allowed to fire, the page is opened again and
    given seconds rather than milliseconds, and opened more than once,
    because a program is allowed to load differently every time. It costs
    page loads only on a program about to be called broken outright.
    """
    if not _worth_pressing(surface):
        return False
    # **Patience against a program that behaves differently each time means
    # looking more than once.** The one here rejects its own load thirty per
    # cent of the time, and its Retry starts a load that rejects just as
    # often, so a single look can find an error, press Retry, get a second
    # error, and end exactly where it started. Three looks is the difference
    # between a false alarm one run in twelve and one nobody has seen. It
    # costs page loads only on a program that is about to be called broken
    # outright.
    for _ in range(SLOW_TRIES):
        if _one_look(engine):
            return True
    return False


def _one_look(engine: Browser) -> bool:
    """Open it, press what it offers, and wait properly. Did anything move?"""
    with contextlib.suppress(Exception):
        with engine.open() as (page, *_):
            before = browser.signature(page)
            # **The page is opened again, so what it offers now is what can
            # be pressed.** One program here rejects its own load thirty per
            # cent of the time by design, so the reopened page is often not
            # the page the surface was measured on: it shows a list where the
            # first load showed an error and a Retry. Pressing selectors from
            # a page that no longer exists presses nothing, nothing moves,
            # and the guard then waves through the very verdict it exists to
            # stop. Measured at roughly one run in five.
            pressable = _worth_pressing(
                from_page(_Shot(browser.elements(page))))
            # **Nothing to press is not evidence of death.** The page this
            # was reopened for offered a Retry because its load had failed;
            # this one loaded and shows the list, so it has a filter box and
            # no buttons at all. Pressing nothing moves nothing, and reading
            # that as confirmation condemned a working program one run in
            # five. A program that comes up differently from the one the
            # surface was measured on is a program the page-level verdict
            # cannot speak for.
            if not pressable:
                return True
            browser.perform(page, [{"click": c.selector} for c in pressable])
            for _ in range(SLOW_LOOKS):
                page.wait_for_timeout(SLOW_POLL_MS)
                if browser.moved(before, browser.signature(page)):
                    return True
    return False


def _drew(shot: Dict[str, Any]) -> bool:
    """Whether any canvas in this measurement holds a picture.

    Anything that is neither empty nor one flat colour edge to edge. A stroke
    on a transparent canvas counts, which is why this cannot be uniformity
    alone: only the ink is measured there, so a black line is a single colour.
    """
    # A page can blind the driver: one generated calculator declares
    # `function eval()`, so every reading comes back as whatever that
    # returns rather than as a measurement. Unreadable is not undrawn.
    if not isinstance(shot, dict):
        return False
    for row in shot.get("canvas") or []:
        if isinstance(row, list) and len(row) > 7 and row[0] > 0 and row[7] == 0:
            return True
    return False


def _nothing_drawn(run: QA, drew: bool, opened: Opened) -> None:
    """A canvas that never showed anything, on a page that was driven.

    **A canvas of one colour is a canvas nobody drew into**, and counting
    non-transparent pixels gets that exactly backwards for WebGL, which starts
    at whatever colour it was cleared to rather than transparent. Three
    wireframe cubes drew twenty-four line indices every frame into a buffer
    that clipped every one of them away, and each measured as 836,000 painted
    pixels out of 836,000: completely full, and showing nothing.

    No single case can say this. The plan demands that a canvas draw only when
    the page offers nothing else to press, and that gate is right: a chart is
    blank until something is typed into the field beside it, and a canvas of
    bouncing balls has no balls until one is added, so demanding an answer
    from either called four working programs dead. What is fair to ask is the
    same question after the whole plan has run. Every control was pressed,
    every field was filled, the canvas was clicked at four points, dragged
    across and driven with the keyboard, and it never once held two colours.

    Guarded exactly as the page-wide verdict is, and for the same reason: if
    there is surface here the plan could not reach, then what was never driven
    may be the only thing that would have drawn.
    """
    if drew or opened.unreached or not opened.surface.canvases:
        return
    acted = [r for r in run.results.values()
             if r.case.acts and r.outcome != UNKNOWN]
    if len(acted) < 2 or any(r.failed for r in run.results.values()):
        return
    _finding(run, "something appears on the canvas", "nothing-drawn",
             f"nothing ever appeared on this canvas: {len(acted)} checks used "
             f"the page and the canvas stayed one flat colour, so whatever "
             f"the program draws is not reaching the screen",
             page_wide=True)


def _nothing_responds(run: QA, answered: set, engine: Browser,
                      unreached: Optional[Dict[str, int]] = None) -> None:
    """A page that answers none of its own controls has nothing behind it.

    This is the only finding here that no single case can make, and it has
    to be that way. A lone button is allowed to do nothing visible: a
    palette swatch selects a colour and says so somewhere the driver cannot
    read, so every case asks only that it survives being pressed, and a
    kanban board whose three `+ Add` buttons are wired to nothing passed
    every one of them.

    What none of them can see is the *page*: three buttons that all promise
    to add something, nothing else to press, and after pressing all of them
    the page is exactly as it loaded. The permission each control gets on
    its own was never meant to be granted to all of them at once.

    Narrow, because the cost of being wrong here is a whole program called
    broken: it needs a page that offered something to press, cases that
    actually pressed it, and **not one observation of anything changing**
    anywhere in the run.

    **And it needs the plan to have been the whole page.** This is a verdict
    on everything, drawn from whatever the plan happened to reach, and the
    count of cases cannot tell those apart: a kanban board with three dead
    `Add` buttons ran fourteen cases and deserved it, and a sortable table
    ran twelve, every one of them a click on a data cell, while the three
    headers that do the sorting were never touched. It said the page answers
    nothing and the page sorted perfectly. So `browser.unreached` is asked
    what the surface rules left behind, and anything at all stands the rule
    down: what is unreached might be the only part that was ever wired.

    Left over, never few. A page that offers nothing because its script died
    on the first line has an empty surface and nothing unreached, and that is
    exactly the page this finding is for.
    """
    if unreached:
        return
    acted = [r for r in run.results.values()
             if r.case.acts and r.outcome != UNKNOWN]
    # **Counted by control, not by case.** This is a verdict on a page that
    # offered several things and answered none of them, and one control
    # pressed twice is one thing pressed twice. A sortable table whose only
    # clickable element is a header gained a second case when cells began
    # being clicked twice, and met a rule it had correctly stood outside of.
    tried = {r.case.control or r.case.id for r in acted}
    if len(tried) < 2 or any(r.case.id in answered for r in acted):
        return
    if run.surface is not None and _waited_out(engine, run.surface):
        return
    _finding(run, "something on the page responds when used",
             "nothing-responds",
             f"nothing on the page changed after any control was used: "
             f"{len(acted)} checks used what the page offers and none of them "
             f"changed it, so the controls do not seem to be connected to "
             f"any code",
             page_wide=True)
