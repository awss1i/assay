"""Tests for how `plan` turns a page's controls into cases, and what it
avoids assuming about them. Each docstring says which wrong result on a
working program the rule prevents.
"""

from __future__ import annotations

from assay.qa import FAILED, QA, Result
from assay.surface import (CANVAS_POINTS, COMMON_GRIDS, SAMPLE_ALIKE, Case,
                           Control, Surface, plan)


def page(*controls: Control) -> Surface:
    return Surface(kind="page", controls=list(controls))


def test_every_control_is_exercised() -> None:
    """Every control on the page gets at least one case, so none goes
    unpressed."""
    surface = page(Control("button", "#clear", "Clear"),
                   Control("button", "#hide", "Hide Grid"),
                   Control("button", "#undo", "Undo"),
                   Control("button", "#redo", "Redo"),
                   Control("button", "#dl", "Download"))

    touched = {c.control for c in plan(surface) if c.control}
    assert touched == {"#clear", "#hide", "#undo", "#redo", "#dl"}, touched


def test_a_button_only_has_to_survive_being_pressed() -> None:
    """A lone button's case only expects that pressing it throws no error. A
    palette swatch that sets the current colour without showing a selection
    changes nothing measurable, and it isn't broken.
    """
    got = [c for c in plan(page(Control("button", "#go", "Go"))) if c.control]

    assert got, "the button was never pressed"
    assert all(c.expect == {"quiet": True} for c in got), [c.expect for c in got]


def test_a_canvas_has_to_respond_to_something() -> None:
    """On a page with nothing else to press, a canvas gets one case that both
    clicks it and presses keys, and expects the canvas to change. A paint tool
    responds to clicks, but a game like snake waits for keys, so a case that
    only clicked would report a working game as broken.
    """
    cases = plan(page(Control("canvas", "#board", "board", True, 480, 480)))
    both = [c for c in cases if c.expect.get("changes")]

    assert len(both) == 1, [c.what for c in cases]
    verbs = {v for step in both[0].acts for v in step}
    assert "click" in verbs and "press" in verbs, verbs
    assert both[0].expect.get("painted"), both[0].expect


def test_a_repeated_control_is_sampled_not_enumerated() -> None:
    """Many identical controls, like the cells of a grid, get `SAMPLE_ALIKE`
    cases between them instead of one each. A case per cell would make the
    plan huge and repeat the same result, while a small sample still catches a
    cell that only works in one corner.
    """
    cells = [Control("button", f"#c{i}", "", True, 20, 20) for i in range(256)]
    cases = plan(page(*cells, Control("button", "#clear", "Clear", True, 60, 30)))

    sampled = {c.control for c in cases if c.control and c.control != "#clear"}
    assert len(sampled) == SAMPLE_ALIKE, sampled
    assert "#clear" in {c.control for c in cases}, "a named button is not alike"


def test_a_disabled_control_is_not_planned_against() -> None:
    """A disabled control gets no case, because doing nothing is correct
    for it."""
    surface = page(Control("button", "#go", "Go", enabled=True),
                   Control("button", "#off", "Off", enabled=False))

    assert {c.control for c in plan(surface) if c.control} == {"#go"}


def test_a_field_is_given_the_awkward_cases() -> None:
    """A text field is filled with awkward values, including an empty one and
    one long enough to overflow."""
    cases = plan(page(Control("text", "#name", "Your name")))
    filled = [a.get("fill") or a["enter"] for c in cases for a in c.acts
              if "fill" in a or "enter" in a]

    assert any(v.endswith("=") for v in filled), "the empty case is missing"
    assert any(len(v) > 200 for v in filled), "the long case is missing"


def test_a_field_and_the_button_beside_it_are_one_gesture() -> None:
    """A field is filled and then the button beside it is pressed, because
    typing without submitting runs no handler."""
    cases = plan(page(Control("text", "#item", "Item"),
                      Control("button", "#add", "Add")))
    paired = [c for c in cases if len(c.acts) == 2
              and "fill" in c.acts[0] and "click" in c.acts[1]]

    assert paired, [c.what for c in cases]
    assert paired[0].expect.get("changes"), paired[0].expect


def test_two_buttons_are_tried_in_both_orders() -> None:
    """Two buttons are pressed in both orders, because Undo then Clear can
    behave differently from Clear then Undo."""
    cases = plan(page(Control("button", "#a", "A"), Control("button", "#b", "B")))
    pairs = {tuple(a["click"] for a in c.acts)
             for c in cases if len(c.acts) == 2 and all("click" in a for a in c.acts)}

    assert ("#a", "#b") in pairs and ("#b", "#a") in pairs, pairs


def test_the_canvas_points_miss_every_common_grid_boundary() -> None:
    """The points assay clicks on a canvas stay clear of the cell boundaries
    of common grid sizes. The centre of a canvas is a boundary on every even
    grid, so a click there lands between cells, and a grid that toggles cells
    correctly would look like it ignored the click.
    """
    for fx, fy in CANVAS_POINTS:
        for across in COMMON_GRIDS:
            for f in (fx, fy):
                into = (f * across) % 1
                margin = min(into, 1 - into)
                assert margin >= 0.18, (f, across, margin)


def test_every_failure_is_reported_and_the_summary_counts_them() -> None:
    """`failing` lists every failed case, and the summary counts them."""
    surface = page(Control("button", "#go", "Go"))
    qa = QA(measure=lambda: surface,
            build_plan=lambda s: plan(s),
            carry_out=lambda case: Result(case, FAILED, "it broke"))
    qa.run()

    assert len(qa.failing) == len(qa.plan) > 0
    assert qa.summary().endswith(f"{len(qa.plan)} failed")


def test_a_field_is_paired_with_the_button_in_its_own_widget() -> None:
    """A field is only paired with a button from the same widget. On a kanban
    board with a box and a "+" button per column, filling one column's box
    and pressing another column's "+" correctly changes nothing.
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


def test_a_number_field_is_typed_a_number() -> None:
    """A number field is filled with digits. A number box rejects text like
    `Sample item`, so the page would correctly do nothing and be reported as
    broken."""
    surface = page(Control("number", "#secs", "Seconds", group=1),
                   Control("button", "#go", "Start", group=1))
    case = next(c for c in plan(surface) if "then press" in c.what)
    typed = next(a["fill"] for a in case.acts if "fill" in a).split("=", 1)[1]

    assert typed.isdigit(), f"typed {typed!r} into a number box"


def test_whether_a_number_box_is_a_setting_depends_on_the_canvas() -> None:
    """On a page with a canvas, filling a number box and pressing its button
    isn't expected to change anything, because the box is a setting like a
    brush size. On a page without one, like a temperature converter, it is.
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
    """A canvas also gets a drag case, because a freehand canvas only
    responds to a press, a move and a release."""
    surface = page(Control("canvas", "#board", "board", 400, 300))
    case = next(c for c in plan(surface) if "drag" in c.what)

    assert any("drag" in a for a in case.acts)


def test_a_field_is_paired_with_the_button_that_follows_it() -> None:
    """A field is only paired with the button right after it. In a todo list,
    Add follows the box and the filter buttons come later, and typing a task
    then pressing All correctly changes nothing.
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
