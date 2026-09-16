"""What a plan is derived from, and what it refuses to assume.

Every case here is a rule that was learned by being wrong about a real
program. The comments say which, because a threshold with no measurement
behind it is a guess that looks like a decision.
"""

from __future__ import annotations

from types import SimpleNamespace

from assay.qa import FAILED, PASSED, QA, Ladder, Result
from assay.surface import (CANVAS_POINTS, COMMON_GRIDS, SAMPLE_ALIKE, Case,
                           Control, Surface, as_acts, plan)


def page(*controls: Control) -> Surface:
    return Surface(kind="page", controls=list(controls))


def test_every_control_is_exercised() -> None:
    """A live paint tool shipped five controls and had criteria for one.

    Clear, Hide Grid, Undo, Redo and Download, and four of five were never
    pressed, because the only plan was seven criteria written before the
    program existed.
    """
    surface = page(Control("button", "#clear", "Clear"),
                   Control("button", "#hide", "Hide Grid"),
                   Control("button", "#undo", "Undo"),
                   Control("button", "#redo", "Redo"),
                   Control("button", "#dl", "Download"))

    touched = {c.control for c in plan(surface) if c.control}
    assert touched == {"#clear", "#hide", "#undo", "#redo", "#dl"}, touched


def test_a_button_only_has_to_survive_being_pressed() -> None:
    """A derived case cannot know what a button *owes*.

    Asserting *something must change* is a guess about design: a palette
    swatch that sets the current colour and shows no selection border changes
    nothing measurable and is not broken. Measured against a paint tool
    verified by hand to work, that assertion produced **nine false failures
    out of twenty-one cases**. What a control owes is what a criterion says.
    """
    got = [c for c in plan(page(Control("button", "#go", "Go"))) if c.control]

    assert got, "the button was never pressed"
    assert all(c.expect == {"quiet": True} for c in got), [c.expect for c in got]


def test_a_canvas_has_to_respond_to_something() -> None:
    """A canvas is driven by whatever that program is driven by.

    Asserting that *clicking* one must change something is right for a paint
    tool and nonsense for a game. A snake that plays correctly, with arrow keys
    moving the centroid the right way for all four, scored 1 of 5 that way,
    because four cases clicked a canvas that waits for a keypress. So one case
    asks the question that is true of every interactive program, and it uses
    the keyboard as well as the mouse.
    """
    cases = plan(page(Control("canvas", "#board", "board", True, 480, 480)))
    both = [c for c in cases if c.expect.get("changes")]

    assert len(both) == 1, [c.what for c in cases]
    verbs = {v for step in both[0].acts for v in step}
    assert "click" in verbs and "press" in verbs, verbs
    assert both[0].expect.get("painted"), both[0].expect


def test_a_repeated_control_is_sampled_not_enumerated() -> None:
    """A grid of 256 clickable cells is one control repeated.

    Planning a case for each produced a **505-case plan** on one program,
    hours of browser launches saying the same thing 250 times. Three of a kind
    catches one that works only in a corner, which is the only way they differ.
    """
    cells = [Control("button", f"#c{i}", "", True, 20, 20) for i in range(256)]
    cases = plan(page(*cells, Control("button", "#clear", "Clear", True, 60, 30)))

    sampled = {c.control for c in cases if c.control and c.control != "#clear"}
    assert len(sampled) == SAMPLE_ALIKE, sampled
    assert "#clear" in {c.control for c in cases}, "a named button is not alike"


def test_a_disabled_control_is_not_planned_against() -> None:
    """It is part of the surface, and nothing happening is correct."""
    surface = page(Control("button", "#go", "Go", enabled=True),
                   Control("button", "#off", "Off", enabled=False))

    assert {c.control for c in plan(surface) if c.control} == {"#go"}


def test_a_field_is_given_the_awkward_cases() -> None:
    """Empty, ordinary, long enough to overflow, and characters that break
    naive parsing. Four cases that between them catch what generated programs
    actually get wrong."""
    cases = plan(page(Control("text", "#name", "Your name")))
    filled = [a["fill"] for c in cases for a in c.acts if "fill" in a]

    assert any(v.endswith("=") for v in filled), "the empty case is missing"
    assert any(len(v) > 200 for v in filled), "the long case is missing"


def test_a_field_and_the_button_beside_it_are_one_gesture() -> None:
    """Typing and never submitting exercises no handler."""
    cases = plan(page(Control("text", "#item", "Item"),
                      Control("button", "#add", "Add")))
    paired = [c for c in cases if len(c.acts) == 2
              and "fill" in c.acts[0] and "click" in c.acts[1]]

    assert paired, [c.what for c in cases]
    assert paired[0].expect.get("changes"), paired[0].expect


def test_two_buttons_are_tried_in_both_orders() -> None:
    """Undo-then-Clear and Clear-then-Undo are different programs."""
    cases = plan(page(Control("button", "#a", "A"), Control("button", "#b", "B")))
    pairs = {tuple(a["click"] for a in c.acts)
             for c in cases if len(c.acts) == 2 and all("click" in a for a in c.acts)}

    assert ("#a", "#b") in pairs and ("#b", "#a") in pairs, pairs


def test_the_canvas_points_miss_every_common_grid_boundary() -> None:
    """The centre of a canvas is a cell boundary for every even grid.

    300 of 600 with twelve columns is exactly 6.0 cells in, so a click there
    lands on a line and a page whose cells toggle perfectly reads as one that
    ignored it. A build measured by hand as correct at four cells had its own
    criterion recorded FAILED for exactly that.
    """
    for fx, fy in CANVAS_POINTS:
        for across in COMMON_GRIDS:
            for f in (fx, fy):
                into = (f * across) % 1
                margin = min(into, 1 - into)
                assert margin >= 0.18, (f, across, margin)


def test_an_act_it_does_not_know_is_dropped_not_guessed() -> None:
    """Performing something nobody asked for is worse than performing
    nothing."""
    assert as_acts([{"click": "#go"}, {"teleport": "#go"}]) == [{"click": "#go"}]
    assert as_acts("not a list") == []


def test_no_repairer_means_no_case_was_given_up_on() -> None:
    """`assay` on its own repairs nothing, so nothing can be unrepairable.

    The loop used to run regardless and `_attend` refused every case for
    want of a repairer, which put all of them in `gave_up`: a clean install
    checking a broken page reported `8 failed, 8 could not be repaired`
    about a program nothing had ever tried to fix. A repair that was never
    attempted must not read like one that was tried and failed.
    """
    surface = page(Control("button", "#go", "Go"))
    qa = QA(measure=lambda: surface,
            build_plan=lambda s: plan(s),
            carry_out=lambda case: Result(case, FAILED, "it broke"))
    qa.run()

    assert qa.failing, "the case really did fail"
    assert qa.gave_up == []
    assert "could not be repaired" not in qa.summary()


def test_a_field_is_paired_with_the_button_in_its_own_widget() -> None:
    """A kanban board has three "New card…" boxes and three "+" buttons.

    Pairing the first box with every button asserts that filling column one
    and pressing column three must change something, which it must not, and
    the board was reported broken for behaving correctly.
    """
    surface = page(
        Control("text", "#a-in", "New card...", group=1),
        Control("button", "#a-add", "+", group=1),
        Control("text", "#b-in", "New card...", group=2),
        Control("button", "#b-add", "+", group=2),
    )
    pairs = [c for c in plan(surface) if "then press" in c.what]

    assert pairs, "the field-and-button gesture is gone"
    for case in pairs:
        filled = next(a["fill"].split("=")[0] for a in case.acts if "fill" in a)
        pressed = next(a["click"] for a in case.acts if "click" in a)
        assert filled[1] == pressed[1], (
            f"{filled} was paired with {pressed}, which is another widget")


def test_a_lone_field_still_reaches_every_button() -> None:
    """Grouping must not cost the ordinary case: one box, one Add."""
    surface = page(Control("text", "#q", "Task"),
                   Control("button", "#add", "Add"))
    assert [c for c in plan(surface) if "then press" in c.what]


def test_a_number_field_is_typed_a_number() -> None:
    """`Sample item` in a number box is rejected, so the page rightly does
    nothing, and the case then reported a working countdown as broken."""
    surface = page(Control("number", "#secs", "Seconds", group=1),
                   Control("button", "#go", "Start", group=1))
    case = next(c for c in plan(surface) if "then press" in c.what)
    typed = next(a["fill"] for a in case.acts if "fill" in a).split("=", 1)[1]

    assert typed.isdigit(), f"typed {typed!r} into a number box"


def test_whether_a_number_box_is_a_setting_depends_on_the_canvas() -> None:
    """Choosing a brush size and pressing Clear is allowed to do nothing.

    Typing a temperature into a converter is not. Both are number boxes, so
    the box cannot settle it: what does is whether the program has a canvas.
    One that has is judged by what happens on it and the boxes around it are
    knobs; one that has not has nowhere else to answer. Asserting on both
    called a working drawing tool broken; asserting on neither let a
    converter that converts nothing through.
    """
    knob = page(Control("number", "#size", "Size", group=1),
                Control("button", "#clear", "Clear", group=1),
                Control("canvas", "#paper", "paper", 300, 200))
    content = page(Control("number", "#c", "Celsius", group=1),
                   Control("button", "#swap", "Swap", group=1))
    words = page(Control("text", "#task", "Task", group=1),
                 Control("button", "#add", "Add", group=1))

    assert not next(c for c in plan(knob)
                    if "then press" in c.what).expect.get("changes")
    assert next(c for c in plan(content)
                if "then press" in c.what).expect.get("changes")
    assert next(c for c in plan(words)
                if "then press" in c.what).expect.get("changes")


def test_a_canvas_is_dragged_on_as_well_as_clicked() -> None:
    """A freehand canvas answers to nothing but press-move-release."""
    surface = page(Control("canvas", "#board", "board", 400, 300))
    case = next(c for c in plan(surface) if "drag" in c.what)

    assert any("drag" in a for a in case.acts)


def test_a_field_is_paired_with_the_button_that_follows_it() -> None:
    """A todo list has Add beside the box and the filters further along.

    Pairing the box with every button asserts that typing a task and then
    pressing *All* must change something, which it must not, and three
    working lists were reported broken for behaving correctly. The button
    that follows the field is the one that takes it.
    """
    surface = page(
        Control("text", "#task", "What needs to be done?", group=1),
        Control("button", "#add", "Add", group=1),
        Control("button", "#all", "All", group=1),
        Control("button", "#done", "Done", group=1),
        Control("button", "#clear", "Clear completed", group=1),
    )
    pairs = [c for c in plan(surface) if "then press" in c.what]

    assert len(pairs) == 1, f"paired with {len(pairs)} buttons, not one"
    assert "Add" in pairs[0].what


def test_a_repair_that_lands_is_re_run_and_recorded() -> None:
    """The loop's whole point, and until now only its refusal was tested.

    `assay` on its own repairs nothing, so the machinery that does had no
    exercise anywhere: a caller supplying `apply` and `ask` was relying on a
    subsystem no test had ever run forwards. This drives one case from
    failing to passing and asserts the three things the loop owes: that the
    change was asked for, that the plan was carried out again afterwards
    rather than just the case being fixed, and that the result says it was
    fixed rather than merely passing.
    """
    surface = page(Control("button", "#go", "Go"))
    mended = {"yet": False}
    carried: list = []

    def carry_out(case: Case) -> Result:
        carried.append(case.id)
        return (Result(case, PASSED, "") if mended["yet"]
                else Result(case, FAILED, "it broke"))

    def ask(result: Result, where: str, ladder: Ladder):
        # The rung is handed over so the caller can ask differently each
        # time; `advice` is the wording that goes with it.
        return {"changes": {"edit": result.case.id, "rung": ladder.rung},
                "why": ladder.advice()}

    def apply(changes, why):
        mended["yet"] = True
        return SimpleNamespace(applied=True, improved=True)

    qa = QA(measure=lambda: surface, build_plan=lambda s: plan(s),
            carry_out=carry_out, apply=apply, ask=ask)
    qa.run()

    assert qa.works, qa.render()
    assert qa.fixed, "a case that came right must be recorded as fixed"
    assert qa.gave_up == []
    assert carried.count(qa.fixed[0]) > 1, "the fixed case was never re-run"
    assert len(set(carried)) == len(qa.plan), "the rest of the plan was skipped"


def test_every_rung_asks_for_something_different() -> None:
    """The ladder is what makes the loop bounded without counting attempts.

    If two rungs asked for the same thing, one of them would be a repeat
    wearing a new name and the loop would spend a turn learning nothing.
    """
    said = [Ladder(at=n).advice() for n in range(len(Ladder.RUNGS))]

    assert len(set(said)) == len(Ladder.RUNGS)
    assert Ladder(at=len(Ladder.RUNGS)).spent
