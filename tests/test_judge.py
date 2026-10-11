"""Tests for how `judge` decides a case from two measurements of a page.
Every verdict rests on these rules, so they're tested as plain comparisons
that run without a browser.
"""

from __future__ import annotations

from assay.browser import (aimed_at_canvas, canvas_still, changed, moved,
                           unpainted)
from assay.qa import FAILED, PASSED
from assay.run import judge
from assay.surface import Case


def sig(canvas=None, text="hello", elements=10, styles=1):
    """One measurement of a page. Each `canvas` row is a seven-number list
    like the one `canvas()` returns."""
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


# Pages that stopped running


def test_a_page_that_threw_fails_whatever_else_held() -> None:
    """An uncaught exception fails the case even when everything else it
    expected held, because the page stopped running at the throw."""
    r = verdict(case(quiet=True), sig(), sig(),
                crashes=["TypeError: x is not a function"])

    assert r.outcome == FAILED
    assert "threw an error and stopped" in r.detail


def test_a_page_that_only_logged_an_error_is_fine() -> None:
    """An error logged with `console.error` doesn't fail the case, because
    the page keeps running after it."""
    assert verdict(case(quiet=True), sig(), sig()).outcome == PASSED


# Acts the page wouldn't accept


def test_an_act_the_page_refused_fails_only_when_nothing_could_be_done() -> None:
    """Acts the page wouldn't accept only fail a case when none of its acts
    could be done. A canvas behind a "press Space to start" overlay can't be
    clicked, and that's the program working.
    """
    two = Case(id="C1", what="use it",
               acts=[{"click": "#a"}, {"press": "Space"}],
               expect={"changes": True})

    some = verdict(two, sig(), sig(text="moved"), could_not=["click #a: timeout"])
    assert some.outcome == PASSED, some.detail
    assert "couldn't" in some.evidence

    none = verdict(two, sig(), sig(),
                   could_not=["click #a: timeout", "press Space: timeout"])
    assert none.outcome == FAILED
    assert "couldn't" in none.detail


def test_a_quiet_case_never_fails_on_a_refused_act() -> None:
    """A `quiet` case only asserts that nothing threw, so an act the page
    wouldn't accept doesn't fail it."""
    r = verdict(case(quiet=True), sig(), sig(), could_not=["click #a: timeout"])

    assert r.outcome == PASSED, r.detail


def test_a_disabled_control_is_reported_and_is_not_a_failure() -> None:
    """Playwright times out on a disabled control the same way as on a missing
    one. assay asks the page which it is, and a disabled control, like Undo
    with nothing to undo, is reported as evidence instead of a failure.
    """
    r = verdict(case(quiet=True), sig(), sig(), was_off=["click #undo"])

    assert r.outcome == PASSED
    assert "disabled" in r.evidence


# Whether anything happened


def test_a_page_that_did_not_move_fails_a_case_that_wanted_movement() -> None:
    assert verdict(case(changes=True), sig(), sig()).outcome == FAILED


def test_a_case_about_nothing_happening_passes_when_nothing_happens() -> None:
    """A case that expects nothing to change, like pressing Add with an empty
    field, passes when nothing changes and fails when something does."""
    assert verdict(case(unchanged=True), sig(), sig()).outcome == PASSED
    assert verdict(case(unchanged=True), sig(),
                   sig(text="a note")).outcome == FAILED


def test_the_canvas_that_was_acted_on_has_to_answer() -> None:
    """When a case clicks a canvas, that canvas has to change, even if text
    elsewhere on the page did. A grid that toggles a cell on both `mousedown`
    and `click` ends where it started while its announcement text changes.
    """
    aimed = Case(id="C1", what="click the canvas",
                 acts=[{"click": "#board canvas@0.2,0.2"}],
                 expect={"changes": True})
    r = verdict(aimed, sig([canvas()]), sig([canvas()], text="Row 1 turned on"))

    assert r.outcome == FAILED
    assert "canvas this check clicked didn't change" in r.detail


def test_a_canvas_nobody_paints_into_is_a_dead_canvas() -> None:
    """A canvas with no painted pixels fails a case that expects painting,
    even when other text changes, like a snake game's score moving over an
    empty board."""
    empty = Case(id="C1", what="use it", acts=[{"press": "Space"}],
                 expect={"changes": True, "painted": True})
    r = verdict(empty, sig([canvas(painted=0)]),
                sig([canvas(painted=0)], text="Score 1"))

    assert r.outcome == FAILED
    assert "1 canvas still shows nothing" in r.detail


def test_wanted_text_that_is_absent_fails() -> None:
    assert verdict(case(want="Total"), sig(), sig(),
                   text="Sum: 4").outcome == FAILED
    assert verdict(case(want="Total"), sig(), sig(text="Total: 4"),
                   text="Total: 4").outcome == PASSED


def test_wanted_text_that_was_already_there_is_not_enough() -> None:
    """Finding the wanted text doesn't pass a case on its own. The page still
    has to change, or a page that does nothing would pass."""
    r = verdict(case(want="Total"), sig(), sig(), text="Total: 4")

    assert r.outcome == FAILED
    assert "nothing on the page changed" in r.detail


# The comparisons


def test_a_brush_stroke_is_seen_even_when_the_mean_cannot_show_it() -> None:
    """One brush stroke on a large opaque canvas moves the rounded mean colour
    by less than 1, so the exact hash decides whether that canvas changed. The
    coarse terms only feed the page-wide check."""
    before = sig([canvas(painted=307200, h=11)])
    after = sig([canvas(painted=307200, h=12)])

    assert canvas_still(before, after) is False
    assert "mean colour stayed the same" in changed(before, after)


def test_a_canvas_that_is_byte_identical_did_not_respond() -> None:
    same = sig([canvas()])
    assert canvas_still(same, sig([canvas()])) is True


def test_a_restyled_element_counts_as_the_page_changing() -> None:
    """A grid built from DOM elements paints a cell by changing its `style`,
    with no new text, no new elements and no canvas, so a style change counts
    as the page changing."""
    said = changed(sig(styles=1), sig(styles=2))

    assert "restyled or recoloured" in said
    assert moved(sig(styles=1), sig(styles=2)) is True


def test_unknown_never_reads_as_did_not_move() -> None:
    """A missing measurement gives None instead of False, so a check that
    didn't run is never reported as a failure."""
    assert moved({}, sig()) is None
    assert moved(sig(), {}) is None


def test_only_an_act_that_names_a_canvas_arms_the_canvas_floor() -> None:
    assert aimed_at_canvas([{"click": "#board canvas@0.2,0.2"}]) is True
    assert aimed_at_canvas([{"press": "ArrowLeft"}]) is False
    assert aimed_at_canvas([{"click": "#start"}]) is False


def test_a_canvas_that_could_not_be_read_is_not_an_empty_one() -> None:
    """A canvas that couldn't be read reports `-1`, which isn't counted as
    unpainted, because the failure was in measuring, not in the program."""
    assert unpainted(sig([[-1, -1, -1, -1, -1, -1, -1]])) == 0
    assert unpainted(sig([canvas(painted=0)])) == 1


# Naming a finding


def test_every_failure_names_the_rule_it_broke() -> None:
    """Each failure records the rule it broke, so the benchmark can match on
    the rule instead of the detail's wording, which changes."""
    threw = verdict(case(quiet=True), sig(), sig(),
                    crashes=["TypeError: x is not a function"])
    still = verdict(case(changes=True), sig(), sig())

    assert threw.rules == ["threw"]
    assert still.rules == ["no-change"]
    assert verdict(case(quiet=True), sig(), sig()).rules == []


def test_a_finding_is_named_without_its_position_in_the_plan() -> None:
    """A finding's key is its rule and what the case did, without the case
    id. Adding a case renumbers every case after it, so a key holding `C016`
    would point at a different case."""
    one = Case(id="C016", what="press Remove, with two saved",
               acts=[{"click": "#go"}], expect={"changes": True})
    two = Case(id="C021", what="press Remove, with two saved",
               acts=[{"click": "#go"}], expect={"changes": True})

    first, second = verdict(one, sig(), sig()), verdict(two, sig(), sig())

    assert first.key == second.key == "no-change@press Remove, with two saved"
