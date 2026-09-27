"""Which findings are the same finding, and which follow a crash on load.

Pure reading of finished results, so none of it needs a browser. Every test
that allows a link has a twin that must not draw one, because a link that
joins two different problems makes a reader fix one and walk past the other.
"""

from __future__ import annotations

from assay.links import attach, family
from assay.qa import FAILED, PASSED, Result
from assay.surface import Case


def failed(case_id: str, what: str, rule: str, detail: str,
           control: str = "", **crash: object) -> Result:
    r = Result(case=Case(id=case_id, what=what, acts=[{"click": control}],
                         control=control),
               outcome=FAILED, detail=detail, rules=[rule])
    for name, value in crash.items():
        setattr(r, name, value)
    return r


def passed(case_id: str, **crash: object) -> Result:
    r = Result(case=Case(id=case_id, what="press Go", acts=[{"click": "#go"}]),
               outcome=PASSED)
    for name, value in crash.items():
        setattr(r, name, value)
    return r


WENT_BACK = ("clicking this twice switched it back off, but the rest of the "
             "page did not change back, so what the first click did is still "
             "in effect")


def test_chips_of_one_bar_are_one_finding() -> None:
    chips = [failed(f"C00{n}", f"click tag{n} twice", "went-back", WENT_BACK,
                    f"#tags > span:nth-child({n})") for n in range(1, 4)]

    attach(chips)

    assert chips[0].links == []
    assert [one.why for one in chips[1].links] == ["same finding as C001"]
    assert [one.to for one in chips[2].links] == ["C001"]


def test_undo_and_redo_are_never_one_finding() -> None:
    """Same rule, same sentence, and two different controls."""
    said = ("pressing this twice from the same starting point: the first "
            "press changed nothing and the second did, so it reacts one press "
            "late")
    undo = failed("C010", "draw twice, then press Undo twice", "one-behind",
                  said, "#undoBtn")
    redo = failed("C011", "draw twice, then press Redo twice", "one-behind",
                  said, "#redoBtn")

    attach([undo, redo])

    assert undo.links == [] and redo.links == []


def test_the_same_crash_from_the_same_place_is_one_finding() -> None:
    boom = dict(crash_message="x is not defined", crash_frame="app.js:4:3")
    one = failed("C001", "open the page", "threw",
                 "the page threw an error and stopped running: x is not defined", **boom)
    two = failed("C002", "press Go", "threw",
                 "the page threw an error and stopped running: x is not defined",
                 "#go", **boom)

    attach([one, two])

    assert [link.to for link in two.links] == ["C001"]


def test_one_message_thrown_from_two_places_is_two_findings() -> None:
    """Two handlers can fail with the same words for different reasons."""
    said = "the page threw an error and stopped running: Cannot read properties of null"
    one = failed("C002", "press Add", "threw", said, "#add",
                 crash_message="Cannot read properties of null",
                 crash_frame="app.js:10:5")
    two = failed("C003", "press Clear", "threw", said, "#clear",
                 crash_message="Cannot read properties of null",
                 crash_frame="app.js:31:9")

    attach([one, two])

    assert one.links == [] and two.links == []


def test_findings_that_differ_only_in_the_names_they_quote_are_one() -> None:
    """Four tabs, each saying its own panel is not shown."""
    tabs = [failed(f"F00{n}", "the panel a selected tab or open section "
                   "controls is shown", "aria",
                   f'"Tab {n}" is marked selected and controls the panel '
                   f'"panel-{n}", but that panel is not shown; first seen at '
                   f'C00{n + 1}') for n in range(1, 4)]

    attach(tabs)

    assert [len(t.links) for t in tabs] == [0, 1, 1]


def test_different_rules_are_never_one_finding() -> None:
    count = failed("F001", "the count of items matches the list",
                   "count-off", "a number on this page reads -1")
    shown = failed("F002", "values typed into a list show up in the new row",
                   "never-shown", "'https://example.com/page' was typed in")

    attach([count, shown])

    assert count.links == [] and shown.links == []


def test_a_page_wide_finding_on_a_page_that_threw_while_loading() -> None:
    boom = dict(crash_message="historyStack is not defined",
                crash_frame="index.html:40:7", crash_at_load=True)
    cases = [failed("C001", "open the page", "threw",
                    "the page threw an error and stopped running: historyStack", **boom),
             failed("C002", "press Undo", "threw",
                    "the page threw an error and stopped running: historyStack",
                    "#undo", **boom)]
    dead = failed("C000", "something on the page responds when used",
                  "nothing-responds", "nothing on the page changed")

    attach(cases + [dead])

    assert [one.kind for one in dead.links] == ["load"]
    assert "(C001)" in dead.links[0].why


def test_no_load_note_when_a_case_ran_on_a_page_that_had_not_thrown() -> None:
    """One case that loaded cleanly means the crash is not the whole story."""
    boom = dict(crash_message="boom", crash_frame="app.js:1:1",
                crash_at_load=True)
    cases = [failed("C001", "open the page", "threw",
                    "the page threw an error and stopped running: boom", **boom),
             passed("C002")]
    dead = failed("C000", "something on the page responds when used",
                  "nothing-responds", "nothing on the page changed")

    attach(cases + [dead])

    assert dead.links == []


def test_a_family_drops_positions_and_keeps_ids() -> None:
    assert family("#grid > tbody:nth-child(2) > tr:nth-child(1) > "
                  "td:nth-child(6)") == "#grid > tbody > tr > td"
    assert family("#undoBtn") != family("#redoBtn")


def test_named_controls_in_one_family_join_only_with_the_same_name() -> None:
    """Chips with their own ids are one family; Undo and Redo are two names."""
    from types import SimpleNamespace as C

    controls = {
        "#t0": C(kind="cell", family="div > span.tag", label="red"),
        "#t1": C(kind="cell", family="div > span.tag", label="blue"),
        "#undo": C(kind="button", family="#bar > button", label="Undo"),
        "#redo": C(kind="button", family="#bar > button", label="Redo"),
    }
    chips = [failed(f"C00{n + 2}", f"click tag{n} twice", "went-back",
                    WENT_BACK, f"#t{n}") for n in range(2)]
    said = "the first press did nothing and the second did something"
    history = [failed("C010", "press Undo twice", "one-behind", said, "#undo"),
               failed("C011", "press Redo twice", "one-behind", said, "#redo")]

    attach(chips + history, controls)

    assert [one.to for one in chips[1].links] == ["C002"]
    assert history[0].links == [] and history[1].links == []
