"""What a page offers, and the plan for exercising all of it.

The plan does what a person testing an unfamiliar page does. It presses every
button, types into every field, and tries empty and unusual input. It's built
from what the browser rendered, not from the markup or a description of the
program.

No model is asked what the page contains, because a model describing a page
it hasn't run is guessing, and its guesses look like real findings.
Acceptance criteria, which say what the program has to do, can be passed in
as cases of their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from assay import browser

#: Kinds of control a plan knows how to exercise. The kind comes from more
#: than the tag, because an ``<input>`` is a textbox, checkbox, slider or
#: button depending on its `type`.
OPERABLE = ("button", "link", "text", "number", "date", "checkbox", "radio",
            "range", "select", "canvas", "color", "file", "handle")

#: A value each of these input types accepts, whatever the label says.
TYPED = {"email": "someone@example.com", "tel": "555-0100",
         "url": "https://example.com/page"}

#: A value each date-like input accepts, in the format its `type` requires.
#: The browser rejects any other format, so the page never sees it.
DATES = {"date": "2026-03-14", "time": "09:30",
         "datetime-local": "2026-03-14T09:30", "month": "2026-03",
         "week": "2026-W11"}


def _typed_for(field: "Control") -> str:
    """A value to type when the aim is to submit the field.

    The value fits the field's type and label. A number box ignores `Sample
    item`, and a field labelled "Enter numbers separated by commas" needs
    numbers, so typing the generic probe and expecting a response would blame
    a working page.
    """
    if field.kind == "number":
        return "25"
    if field.kind == "date":
        return DATES.get(field.input_type, DATES["date"])
    # The input type wins over the label. An email box rejects a sentence
    # whatever it's labelled.
    if field.input_type in TYPED:
        return TYPED[field.input_type]
    answer = browser.sample_for(field.label or field.selector)
    # `sample_for` also answers `prompt` dialogs, where one number is right.
    # A field can take a list, which a chart's input needs.
    return "5, 12, 3, 20" if answer == "5" else answer


#: Values to type into a text field. They cover an empty value, an ordinary
#: one, one long enough to overflow a layout, and one with characters that
#: break naive parsing and HTML escaping.
TEXT_PROBES = (
    ("empty", ""),
    ("ordinary", "Sample item"),
    ("long", "x" * 300),
    ("awkward", "a,b <b>&amp;</b> 'q' \"d\" 1/2"),
)


@dataclass
class Control:
    """One thing a person can operate, as the browser laid it out."""

    kind: str
    selector: str
    label: str = ""
    #: Moves only through the HTML5 drag protocol.
    grabbed: bool = False
    enabled: bool = True
    width: int = 0
    height: int = 0
    #: Which widget it belongs to, or 0 for none. See `Element.group`.
    group: int = 0
    #: The form it sits in, or failing that its container. See
    #: `Element.pairing`.
    pairing: int = 0
    #: Whether the page refuses typing into it, which makes it an output.
    readonly: bool = False
    #: An `<input>`'s own `type`. See `Element.input_type`.
    input_type: str = ""
    #: The `name` a radio shares with the rest of its choices.
    radio: str = ""
    #: Where it sits. See `Element.family`.
    family: str = ""

    @property
    def name(self) -> str:
        """What to call it in a sentence."""
        return self.label or self.selector


@dataclass
class Case:
    """One test, with what to do and what has to be true afterwards.

    ``expect`` only states what a machine can check, like "something must
    change", "this text must appear" or "nothing may throw". Whether the
    change was the right one is left to the criteria and the reader.
    """

    id: str
    what: str
    acts: List[Dict[str, str]] = field(default_factory=list)
    expect: Dict[str, Any] = field(default_factory=dict)
    #: ``derived`` comes from the measured surface, ``seeded`` from the
    #: controls the page adds once it holds something, and ``criterion`` from
    #: the caller.
    origin: str = "derived"
    #: The control it exercises, or blank for a case about the whole page.
    control: str = ""

    def render(self) -> str:
        """One line for the record."""
        return f"{self.id}: {self.what}"


@dataclass
class Surface:
    """Everything the page offers, as measured in the browser."""

    kind: str = ""
    controls: List[Control] = field(default_factory=list)
    #: Why nothing could be measured, when nothing could.
    unavailable: str = ""

    @property
    def operable(self) -> List[Control]:
        """Enabled controls other than canvases, in page order."""
        return [c for c in self.controls
                if c.kind in OPERABLE and c.enabled and c.kind != "canvas"]

    @property
    def canvases(self) -> List[Control]:
        """Canvases, which are operated by position rather than by name."""
        return [c for c in self.controls if c.kind == "canvas"]

    def render(self) -> str:
        """The inventory as text, one control per line."""
        if self.unavailable:
            return f"assay couldn't read the page's controls, {self.unavailable}"
        if not self.controls:
            return ("The page has nothing to use. It has no buttons, fields "
                    "or canvases, and nothing to run.")
        out = [f"kind: {self.kind or 'unknown'}"]
        for c in self.controls:
            if not c.kind:
                continue
            size = f" {c.width}x{c.height}" if c.width else ""
            state = "" if c.enabled else " (disabled)"
            out.append(f"- {c.kind}{state} `{c.selector}`"
                       + (f" {c.label!r}" if c.label else "") + size)
        return "\n".join(out)


def from_page(shot) -> Surface:
    """The surface of a page, from what the browser rendered.

    Controls the page builds at run time count, and controls that aren't
    visible don't.
    """
    if getattr(shot, "unavailable", ""):
        return Surface(kind="page", unavailable=str(shot.unavailable))
    controls = [
        Control(kind=e.kind, selector=e.selector, label=e.label,
                grabbed=e.grabbed,
                enabled=e.enabled, width=e.width, height=e.height,
                group=getattr(e, "group", 0),
                pairing=getattr(e, "pairing", 0),
                readonly=bool(getattr(e, "readonly", False)),
                input_type=str(getattr(e, "input_type", "") or ""),
                radio=str(getattr(e, "radio", "") or ""),
                family=str(getattr(e, "family", "") or ""))
        for e in getattr(shot, "elements", ())
        if getattr(e, "kind", "") and e.visible]
    return Surface(kind="page", controls=controls)


#: Fractions of a canvas's width and height to act at. The centre of an even
#: grid is a cell boundary, so a click there can land on a line and make a
#: working page look broken. Both values stay at least a fifth of a cell away
#: from every cell edge on each grid in `COMMON_GRIDS`, whatever the canvas
#: size. `CANVAS_POINTS` combines them into four points.
SAFE_LOW, SAFE_HIGH = 0.22, 0.78

#: Column counts that grid-based pages commonly use. `SAFE_LOW` and
#: `SAFE_HIGH` are chosen to clear the cell edges of all of them.
COMMON_GRIDS = (8, 10, 12, 15, 16, 20, 25)

#: Where a second stroke starts, top right, so it runs down and left and
#: crosses the first stroke instead of retracing it. A retraced line changes
#: nothing, so a working canvas would look broken.
SECOND_STROKE = (SAFE_HIGH, SAFE_LOW)

#: Where to try the second stroke before deciding a canvas has stopped
#: drawing. Some canvases respond only in some places, like a palette that
#: reacts to a stroke on a shape and ignores the background, so one miss
#: proves nothing. The canvas fails only if none of these draw. A canvas whose
#: drawing buffer covers only a quarter of it still fails all of them.
SECOND_TRIES = ((SAFE_HIGH, SAFE_LOW), (0.5, 0.5), (SAFE_HIGH, SAFE_HIGH))

CANVAS_POINTS = ((SAFE_LOW, SAFE_LOW), (SAFE_HIGH, SAFE_LOW),
                 (SAFE_LOW, SAFE_HIGH), (SAFE_HIGH, SAFE_HIGH))


#: How many of a repeated control to exercise. A grid of clickable `<div>`s
#: can have hundreds of identical cells, and a case for each makes the run far
#: longer without finding more. Three catch a control that only works in one
#: part of the grid.
SAMPLE_ALIKE = 3


def _sampled(controls: List[Control]) -> List[Control]:
    """Every distinct control, and at most `SAMPLE_ALIKE` of any repeated one.

    Controls are alike when they share a kind, label and size, so a `Clear`
    and an `Undo` button are two controls. The sample is spread across each
    group instead of taken from the front, because a grid whose later rows
    aren't wired up is a common fault.
    """
    # Cells are grouped without their label. A cell's text is game state, and
    # some pages label cells from their own `id`, which would make every cell
    # distinct.
    groups: Dict[tuple, List[int]] = {}
    for i, c in enumerate(controls):
        key = ((c.kind, c.width, c.height) if c.kind == "cell"
               else (c.kind, c.label, c.width, c.height))
        groups.setdefault(key, []).append(i)
    keep = set()
    for where in groups.values():
        if len(where) <= SAMPLE_ALIKE:
            keep.update(where)
            continue
        # Keep the first two, because a board that alternates players needs a
        # second move to show it, and spread the rest out to the last one.
        keep.update(where[:2])
        step = (len(where) - 1) / (SAMPLE_ALIKE - 2)
        keep.update(where[round(step * n)] for n in range(1, SAMPLE_ALIKE - 1))
    return [c for i, c in enumerate(controls) if i in keep]


def plan(surface: Surface, criteria: Sequence[Any] = ()) -> List[Case]:
    """Every case worth running on this page, derived from what it offers.

    Criteria come first because they're what the program has to do. Derived
    cases follow, because a page that meets its criteria but breaks on its own
    buttons is still broken. A derived case only states what a machine can
    check, such as that nothing threw or that something changed.
    """
    # Only criteria given as `Case`s are kept, because a criterion needs
    # acts written by its author. One without acts would run as an empty
    # probe and report nothing useful.
    cases: List[Case] = [c for c in criteria if isinstance(c, Case)]
    n = 0

    def add(what: str, acts: List[Dict[str, str]], expect: Dict[str, Any],
            control: str = "") -> None:
        nonlocal n
        n += 1
        cases.append(Case(id=f"C{n:03d}", what=what, acts=acts, expect=expect,
                          control=control))

    if surface.kind != "page":
        return cases

    # Opening the page is a case of its own, because a page that throws on
    # load fails before any control is reached.
    add("open the page and let it settle", [], {"quiet": True})

    handles = [c for c in surface.operable if c.kind == "handle"]
    for c in _sampled(surface.operable):
        if c.kind in ("button", "link"):
            # `quiet`, because a derived case can't know what a button should
            # do. A palette swatch that sets the current colour can change
            # nothing visible and still work, so requiring a change would
            # report false failures. The case still catches a button that
            # throws or can't be pressed, and the measurement is recorded
            # either way. What a button should do belongs in a criterion.
            add(f"press {c.name}", [{"click": c.selector}], {"quiet": True},
                c.selector)
            # Twice, because state machines often break on the second press,
            # like undo after undo or a toggle that only works one way. Only
            # a throw fails it.
            add(f"press {c.name} twice",
                [{"click": c.selector}, {"click": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind in ("text", "number", "date") and not c.readonly:
            # Number and date fields only get values they accept, because the
            # browser refuses letters in them and the case would test
            # nothing. They skip the long and awkward probes, and the
            # ordinary probe becomes a valid value.
            for label, value in TEXT_PROBES:
                if c.kind in ("number", "date"):
                    if label in ("long", "awkward"):
                        continue
                    value = value and _typed_for(c)
                noun = {"number": "number", "date": "date"}.get(c.kind, "text")
                add(f"put {label} {noun} in {c.name}",
                    [{"enter": f"{c.selector}={value}"}], {"quiet": True},
                    c.selector)
        elif c.kind == "handle":
            # A handle has to be dragged. Clicking a split pane's divider or a
            # reorderable row does nothing.
            if c.grabbed:
                # A `draggable` row only moves through the HTML5 drag
                # protocol, which needs a drop target. Reorder lists usually
                # drop before the target, so dropping onto the next row leaves
                # the order unchanged. Drop onto the handle at the far end of
                # the list instead.
                at = [h.selector for h in handles].index(c.selector)
                other = (handles[0] if at * 2 >= len(handles)
                         else handles[-1])
                other = None if other.selector == c.selector else other
                if other is not None:
                    add(f"drag {c.name} onto {other.name}",
                        [{"dragonto": f"{c.selector}>>{other.selector}"}],
                        {"changes": True}, c.selector)
            else:
                add(f"drag {c.name}", [{"drag": c.selector}],
                    {"changes": True}, c.selector)
                # Drag twice and measure only the second drag. A divider that
                # moves once and then can't be grabbed again is a common
                # fault, and measuring both drags together would let the first
                # drag's change hide the second one's failure.
                add(f"drag {c.name}, then drag it again",
                    [{"drag": c.selector}, {"drag": c.selector}],
                    {"changes": True, "second": True}, c.selector)

        elif c.kind == "range":
            # `quiet` for the same reason as a button. Moving the slider still
            # lets the page-wide check tell a page that ignores input from
            # one nobody used.
            add(f"move {c.name}", [{"slide": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind in ("checkbox", "radio"):
            add(f"tick {c.name}", [{"click": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind == "select":
            add(f"choose something in {c.name}", [{"choose": c.selector}],
                {"quiet": True}, c.selector)
        elif c.kind == "color":
            add(f"choose a colour in {c.name}", [{"recolour": c.selector}],
                {"quiet": True}, c.selector)
        elif c.kind == "file":
            add(f"attach a file to {c.name}", [{"attach": c.selector}],
                {"quiet": True}, c.selector)

    # Cells are sampled like buttons, because they're interchangeable and a
    # board can have hundreds. They're `quiet` for the same reason as a
    # button, since clicking a mine is meant to end the game. Clicking them
    # still lets `_nothing_responds` tell a page that ignores input from one
    # nobody used.
    cells = [c for c in surface.controls if c.kind == "cell" and c.enabled]
    for c in _sampled(cells):
        add(f"click {c.name or c.selector}", [{"click": c.selector}],
            {"quiet": True}, c.selector)
        # A cell is the one control that should change itself when pressed,
        # so this compares the two presses' effects on the cell itself. A
        # cell that responds to the second click but not the first is one
        # behind. It's `quiet` too, so a cell the driver can't click, like a
        # flashcard's rotated back face, isn't a failure.
        add(f"click {c.name or c.selector} twice",
            [{"click": c.selector}, {"click": c.selector}],
            {"same_each": True, "itself": True, "quiet": True}, c.selector)
    if len(cells) > 1:
        add(f"click {cells[0].name or 'one cell'}, then the one beside it",
            [{"click": cells[0].selector}, {"click": cells[1].selector}],
            {"quiet": True}, cells[0].selector)

    # Each program drives its canvas differently. A paint tool responds to
    # clicks and a game to keys, so a click alone can't be required to change
    # anything. The point clicks only have to not throw, and one case combines
    # clicks, keys and a drag and asks whether the canvas responds to any of
    # them.
    for c in surface.canvases:
        for i, (fx, fy) in enumerate(CANVAS_POINTS, 1):
            add(f"click {c.name} at point {i}",
                [{"click": f"{c.selector}@{fx},{fy}"}], {"quiet": True},
                c.selector)
        add(f"use {c.name}: click it, drag on it, and press Space, Right "
            f"Arrow, Down Arrow and Enter",
            [{"click": f"{c.selector}@{CANVAS_POINTS[0][0]},{CANVAS_POINTS[0][1]}"},
             {"click": f"{c.selector}@{CANVAS_POINTS[3][0]},{CANVAS_POINTS[3][1]}"},
             {"press": "Space"}, {"wait": "0.4"},
             {"press": "ArrowRight"}, {"wait": "0.3"},
             {"press": "ArrowDown"}, {"wait": "0.3"},
             {"press": "Enter"}, {"wait": "0.4"},
             {"drag": c.selector}],
            # Required to change only when the page has no other controls.
            # A chart draws when you press Add, and a bouncing-balls canvas
            # is empty until you add a ball, so poking those canvases
            # directly proves nothing.
            ({"changes": True, "painted": True} if not surface.operable
             else {"quiet": True}), c.selector)

        # A canvas that took the first stroke has to take the second. Some
        # painters draw one line and ignore the rest, which no other case
        # catches, because the first stroke's change satisfies a comparison
        # of the whole case. A canvas that doesn't respond to the first
        # stroke, like a chart, isn't held to the second.
        add(f"draw on {c.name}, then draw somewhere else on it",
            [{"drag": f"{c.selector}@{SAFE_LOW},{SAFE_LOW}"}]
            + [{"drag": f"{c.selector}@{x},{y}"} for x, y in SECOND_TRIES],
            {"again": True}, c.selector)

        # A button that responds only to its second press is one behind, like
        # an undo that does nothing first and then removes one stroke. The
        # presses start from a canvas with something drawn on it, because a
        # button with nothing to act on is correctly inert. It takes two
        # strokes, because a history that's one behind restores the state
        # it's already in when only one stroke exists, and both presses would
        # look inert.
        for b in surface.operable:
            if b.kind not in ("button", "link"):
                continue
            add(f"draw on {c.name} twice, then press {b.name} twice",
                [{"drag": f"{c.selector}@{SAFE_LOW},{SAFE_LOW}"},
                 {"drag": f"{c.selector}@{SECOND_STROKE[0]},{SECOND_STROKE[1]}"},
                 {"click": b.selector}, {"click": b.selector}],
                {"same_each": True}, b.selector)

    # A field and its submit button are one gesture, so they're tested
    # together. A field pairs with a button in its own widget, because a
    # kanban board can have a box and a + button per column, and filling one
    # column's box then pressing another column's button correctly does
    # nothing. A field only pairs with a button outside its widget when it's
    # the page's only field and its widget has no button. Readonly fields are
    # outputs, like a password generator's result box, so they're skipped.
    fields = [c for c in surface.operable
              if c.kind in ("text", "number", "date") and not c.readonly]
    buttons = [c for c in surface.operable if c.kind == "button"]
    if fields and buttons:
        order = {c.selector: i for i, c in enumerate(surface.controls)}

        def nearest(field: Control, choices: List[Control]) -> List[Control]:
            """The button a person would press after typing in this field.

            That's the first button after the field in the same form or
            container. Other buttons nearby, like a todo list's filters,
            aren't expected to react to the typed text. When no button
            follows the field there's no pair, because a button before it,
            like Clear completed on a list submitted with Enter, may have
            nothing to do with it.
            """
            at = order.get(field.selector, 0)
            # A button with no known form or container can still pair.
            with_it = [b for b in choices
                       if not (b.pairing and field.pairing)
                       or b.pairing == field.pairing]
            after = sorted((b for b in with_it if order.get(b.selector, 0) > at),
                           key=lambda b: order.get(b.selector, 0))
            return after[:1]

        for field in fields[:3]:
            near = [b for b in buttons if b.group and b.group == field.group]
            alone = len(fields) == 1 and not near
            for b in nearest(field, near or (buttons if alone else [])):
                # Submitting typed content has to change the page. A number
                # or date field on a page with a canvas is usually a setting,
                # like a brush size, and pressing Clear on an empty canvas
                # after choosing one correctly changes nothing. Those cases
                # are `quiet`, and the canvas cases judge the page.
                setting = field.kind != "text" and bool(surface.canvases)
                expect = {"quiet": True} if setting else {"changes": True}
                # Fill every field in the widget, because a form can rightly
                # refuse to submit while a required field is empty. The case
                # is still named for this field.
                fills = [{"fill": f"{other.selector}={_typed_for(other)}"}
                         for other in fields
                         if other.group == field.group or other is field]
                # Pick the first option of each radio group in the widget,
                # because a form can rightly refuse to submit without a
                # choice, like a rating with no star.
                sets: Dict[str, Control] = {}
                for choice in surface.operable:
                    if (choice.kind == "radio" and choice.radio
                            and choice.group == field.group):
                        sets.setdefault(choice.radio, choice)
                picks = [{"pick": c.selector} for c in sets.values()]
                # Choose something in each dropdown in the widget too, for
                # the same reason.
                picks += [{"choose": c.selector} for c in surface.operable
                          if c.kind == "select" and c.group
                          and c.group == field.group]
                add(f"type into {field.name}, then press {b.name}",
                    picks + fills + [{"click": b.selector}], expect,
                    b.selector)

    # Each pair of buttons in both orders, because Undo then Clear and Clear
    # then Undo can behave differently. Capped at the first three buttons,
    # because the number of pairs grows with the square of the button count.
    for a in buttons[:3]:
        for b in buttons[:3]:
            if a.selector == b.selector:
                continue
            add(f"press {a.name}, then {b.name}",
                [{"click": a.selector}, {"click": b.selector}], {"quiet": True})
    return cases
