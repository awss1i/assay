"""What separates a program that is broken from one that merely looks odd.

Everything here is a pure comparison of two measurements, so none of it needs
a browser. That is deliberate: the judging is the part every verdict rests on,
and a rule you can only exercise by launching Chromium is a rule that stops
being exercised.
"""

from __future__ import annotations

from assay.browser import (aimed_at_canvas, canvas_still, changed, moved,
                           unpainted)
from assay.qa import FAILED, PASSED
from assay.run import judge
from assay.surface import Case


def sig(canvas=None, text="hello", elements=10, styles=1):
    """One measurement of a page. `canvas` rows are the seven-term form."""
    return {"canvas": list(canvas or []), "text": text,
            "elements": elements, "styles": styles}


def canvas(painted=1000, cx=50, cy=50, r=200, g=200, b=200, h=7):
    return [painted, cx, cy, r, g, b, h]


def case(**expect):
    return Case(id="C001", what="do the thing",
                acts=[{"click": "#go"}], expect=expect or {"quiet": True})


def verdict(c, before, after, crashes=(), could_not=(), was_off=(), text=""):
    return judge(c, before, after, list(crashes), list(could_not),
                 list(was_off), text)


# -- a page that stopped running ---------------------------------------------


def test_a_page_that_threw_fails_whatever_else_held() -> None:
    """An uncaught exception stops execution.

    Everything the page was going to do after that line did not happen, so
    whatever else the case asserted, it asserted about a program that had
    stopped. A build's `A1`, *"a canvas displaying a 10 x 10 grid"*, was
    marked verified against a canvas of zero painted pixels whose only module
    had died on its first call, because the check asked whether a canvas was
    on the page and it was.
    """
    r = verdict(case(quiet=True), sig(), sig(),
                crashes=["TypeError: x is not a function"])

    assert r.outcome == FAILED
    assert "threw and stopped" in r.detail


def test_a_page_that_only_logged_an_error_is_fine() -> None:
    """A page is free to `console.error` and work.

    Collapsing a log line and a throw into one list is what let the above
    through, because the rule written for the first was applied to the second,
    which
    is its opposite.
    """
    assert verdict(case(quiet=True), sig(), sig()).outcome == PASSED


# -- acts the page would not accept ------------------------------------------


def test_an_act_the_page_refused_fails_only_when_nothing_could_be_done() -> None:
    """A canvas behind a "press Space to start" overlay cannot be clicked.

    That is the program working. A snake game that plays correctly, with arrow
    keys moving the centroid the right way for all four, scored 1 of 5
    because four cases clicked through a start overlay and the timeout was
    called a defect.
    """
    two = Case(id="C1", what="use it",
               acts=[{"click": "#a"}, {"press": "Space"}],
               expect={"changes": True})

    some = verdict(two, sig(), sig(text="moved"), could_not=["click #a: timeout"])
    assert some.outcome == PASSED, some.detail
    assert "could not" in some.evidence

    none = verdict(two, sig(), sig(),
                   could_not=["click #a: timeout", "press Space: timeout"])
    assert none.outcome == FAILED
    assert "could not" in none.detail


def test_a_quiet_case_never_fails_on_a_refused_act() -> None:
    """`quiet` asserts that the program survives being used this way, and an
    act the page would not accept is not the program misbehaving."""
    r = verdict(case(quiet=True), sig(), sig(), could_not=["click #a: timeout"])

    assert r.outcome == PASSED, r.detail


def test_a_disabled_control_is_reported_and_is_not_a_failure() -> None:
    """Playwright times out on a disabled control exactly as on a missing one.

    A working build's Undo, correctly disabled with nothing to undo, was
    reported as a defect, and which of the two it is, is a fact the page can
    be asked for.
    """
    r = verdict(case(quiet=True), sig(), sig(), was_off=["click #undo"])

    assert r.outcome == PASSED
    assert "disabled" in r.evidence


# -- did anything happen -----------------------------------------------------


def test_a_page_that_did_not_move_fails_a_case_that_wanted_movement() -> None:
    assert verdict(case(changes=True), sig(), sig()).outcome == FAILED


def test_a_case_about_nothing_happening_passes_when_nothing_happens() -> None:
    """*"Click Add while the field is empty → no new note is added"* is a
    criterion about **nothing**, and reading a missing expectation as
    *something must change* failed a program for correctly doing nothing."""
    assert verdict(case(unchanged=True), sig(), sig()).outcome == PASSED
    assert verdict(case(unchanged=True), sig(),
                   sig(text="a note")).outcome == FAILED


def test_the_canvas_that_was_acted_on_has_to_answer() -> None:
    """The page-wide floor is a whole-*page* test.

    A grid announced *"Row 1 Column 1 turned on"* into a live region on every
    click, so the text moved while the cell being announced did not: the click
    toggled twice, once on `mousedown` and once on `click`, and landed back
    where it started.
    """
    aimed = Case(id="C1", what="click the canvas",
                 acts=[{"click": "#board canvas@0.2,0.2"}],
                 expect={"changes": True})
    r = verdict(aimed, sig([canvas()]), sig([canvas()], text="Row 1 turned on"))

    assert r.outcome == FAILED
    assert "canvas you acted on is unchanged" in r.detail


def test_a_canvas_nobody_paints_into_is_a_dead_canvas() -> None:
    """It shows the same as one that was never there.

    Two snake games passed coverage 18-of-18 and 7-of-8 with zero painted
    pixels, their scoreboards moving while the board stayed empty.
    """
    empty = Case(id="C1", what="use it", acts=[{"press": "Space"}],
                 expect={"changes": True, "painted": True})
    r = verdict(empty, sig([canvas(painted=0)]),
                sig([canvas(painted=0)], text="Score 1"))

    assert r.outcome == FAILED
    assert "nothing drawn" in r.detail


def test_wanted_text_that_is_absent_fails() -> None:
    assert verdict(case(want="Total"), sig(), sig(),
                   text="Sum: 4").outcome == FAILED
    assert verdict(case(want="Total"), sig(), sig(text="Total: 4"),
                   text="Total: 4").outcome == PASSED


def test_wanted_text_that_was_already_there_is_not_enough() -> None:
    """You did something and the page did not move.

    A case that only asks whether some text is on the page is a case that
    would pass on a dead one, which is the failure this whole thing exists
    for. Finding the text you wanted does not excuse the program from having
    responded, so the movement floor still applies.
    """
    r = verdict(case(want="Total"), sig(), sig(), text="Total: 4")

    assert r.outcome == FAILED
    assert "nothing on the page changed" in r.detail


# -- the comparisons themselves ----------------------------------------------


def test_a_brush_stroke_is_seen_even_when_the_mean_cannot_show_it() -> None:
    """A 640x480 opaque canvas has 307,200 painted pixels and one stroke moves
    the rounded mean by less than 1, so the exact hash decides whether *this
    canvas* responded, where the coarse terms decide the page-wide floor."""
    before = sig([canvas(painted=307200, h=11)])
    after = sig([canvas(painted=307200, h=12)])

    assert canvas_still(before, after) is False
    assert "less than the painted count" in changed(before, after)


def test_a_canvas_that_is_byte_identical_did_not_respond() -> None:
    same = sig([canvas()])
    assert canvas_still(same, sig([canvas()])) is True


def test_a_restyled_element_counts_as_the_page_changing() -> None:
    """A grid built from DOM elements paints a cell by setting its `style`:
    same text, same element count, and no canvas to measure at all."""
    said = changed(sig(styles=1), sig(styles=2))

    assert "restyled or recoloured" in said
    assert moved(sig(styles=1), sig(styles=2)) is True


def test_unknown_never_reads_as_did_not_move() -> None:
    """Recording a measurement that never happened as a failure sends a
    repair after a check that did not run."""
    assert moved({}, sig()) is None
    assert moved(sig(), {}) is None


def test_only_an_act_that_names_a_canvas_arms_the_canvas_floor() -> None:
    assert aimed_at_canvas([{"click": "#board canvas@0.2,0.2"}]) is True
    assert aimed_at_canvas([{"press": "ArrowLeft"}]) is False
    assert aimed_at_canvas([{"click": "#start"}]) is False


def test_a_canvas_that_could_not_be_read_is_not_an_empty_one() -> None:
    """`-1` is *could not be read*, and reporting it as unpainted would be a
    finding about the harness dressed as one about the program."""
    assert unpainted(sig([[-1, -1, -1, -1, -1, -1, -1]])) == 0
    assert unpainted(sig([canvas(painted=0)])) == 1
