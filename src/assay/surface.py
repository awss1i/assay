"""What the artefact offers, and the plan for exercising all of it.

**The check stage read source code instead of using the program.** Measured
across every build on disk: **219 of 258 acceptance criteria were never carried
out (85%), and one build spent 38 steps of which fifteen were refusals,
four were reads and **none** was a verify. Five of the investigator's seven
verbs inspect code, a coding model's gradient is to read code, and the loop let
it. Scavenging is unbounded (643 static errors across the builds) and
uncorrelated with whether the program works: `r4a_clicker` reports every task
failed and works perfectly.

A person testing a program does the opposite. They press every button, type
into every field, try the empty case and the silly case, and only read source
once using it has shown them something wrong.

Two documents, two jobs, and the factory only ever had the first:

===================  ==========================  ==========================
                     acceptance criteria         the test plan
===================  ==========================  ==========================
says                 what the program **owes**   how to exercise what it has
written              before any code, from spec  after the build, from this
size                 five to seven               dozens
===================  ==========================  ==========================

The criteria being written before the skeleton is right and stays: an agent
that has read the code writes claims the code already satisfies. That is an
argument about a contract. It is not an argument against coverage: a
live paint tool shipped with Clear, Hide Grid, Undo, Redo and Download, and
**four of its five controls had no criterion and were never pressed once**.

Everything here is derived from what was measured. Nothing asks a model what
the program contains, for the reason the probe planner and the cross-evaluator
were both deleted: an agent describing work it has not seen is guessing, and
its guess is indistinguishable from a finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from assay import browser

#: Kinds of control a plan knows how to exercise. A tag is not enough:
#: ``<input>`` is a textbox, a checkbox, a slider or a button depending on one
#: attribute, and a plan that treats them alike types into a checkbox.
OPERABLE = ("button", "link", "text", "number", "checkbox", "radio", "range",
            "select", "canvas", "color", "handle")

#: Values worth putting into a text field. Not a fuzz list. Four cases that
#: between them catch the faults generated programs actually have: nothing at
#: all, something ordinary, something long enough to overflow a layout, and
#: something whose characters break naive parsing and naive HTML.
#: What to type into a field when the point is to submit it rather than to
#: probe it. A number box rejects `Sample item` and correctly does nothing
#: with it, so a case that types that and then asserts the page must respond
#: is asserting about an input the program was right to ignore. It reported a
#: working countdown timer as broken.
def _typed_for(field: "Control") -> str:
    """What to type in, reading the words on the box.

    A field saying *Enter numbers separated by commas* is asking for numbers,
    and `Sample item` is not an answer to it. A chart given that correctly
    drew nothing, and the case then blamed the chart. This is only what a
    person does before typing: read the label.
    """
    if field.kind == "number":
        return "25"
    answer = browser.sample_for(field.label or field.selector)
    # A box is allowed several values where a `prompt` takes one: a chart
    # wants a series, and a dialog asking *how many* wants a number.
    return "5, 12, 3, 20" if answer == "5" else answer


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
    #: Which widget it belongs to; 0 when it is in none. See `Element.group`.
    group: int = 0
    #: The form, or failing that the container, it sits in. See
    #: `Element.pairing`.
    pairing: int = 0
    #: Whether the page refuses typing into it, which makes it an output.
    readonly: bool = False

    @property
    def name(self) -> str:
        """What to call it in a sentence."""
        return self.label or self.selector


@dataclass
class Case:
    """One test: what to do, and what has to be true afterwards.

    ``expect`` is deliberately thin. The machine can say *something must
    change, this text must appear, nothing may throw. It cannot say
    whether the thing that changed was the right thing. That half stays with
    the criteria and with the investigator reading the numbers, which is the
    same split `screen.quality` already makes.
    """

    id: str
    what: str
    acts: List[Dict[str, str]] = field(default_factory=list)
    expect: Dict[str, Any] = field(default_factory=dict)
    #: ``derived`` comes from the measured surface. ``criterion`` is a
    #: contract rather than coverage. ``model`` is a case only judgement
    #: finds, asked for by name.
    origin: str = "derived"
    #: Which control it exercises, when it exercises one. Blank for a case
    #: about the artefact as a whole.
    control: str = ""

    def render(self) -> str:
        """One line for the record."""
        return f"{self.id}: {self.what}"


@dataclass
class Surface:
    """Everything the artefact offers, measured rather than described."""

    kind: str = ""
    controls: List[Control] = field(default_factory=list)
    #: Why there is nothing here, when there is nothing here.
    unavailable: str = ""

    @property
    def operable(self) -> List[Control]:
        """Controls a person could actually work, in a stable order."""
        return [c for c in self.controls
                if c.kind in OPERABLE and c.enabled and c.kind != "canvas"]

    @property
    def canvases(self) -> List[Control]:
        """Canvases, which are operated by position rather than by name."""
        return [c for c in self.controls if c.kind == "canvas"]

    def render(self) -> str:
        """The inventory, for the record and for a prompt."""
        if self.unavailable:
            return f"The surface could not be measured: {self.unavailable}"
        if not self.controls:
            return ("Nothing on this artefact can be operated: no button, no "
                    "field, no canvas, and nothing to run. That is itself a "
                    "finding for anything a person is meant to use.")
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
    """The surface of a page, from what the browser actually rendered.

    Not from the markup: a control the page builds at run time is as real as
    one written in the HTML, and a control the CSS hides is not there at all.
    """
    if getattr(shot, "unavailable", ""):
        return Surface(kind="page", unavailable=str(shot.unavailable))
    controls = [
        Control(kind=e.kind, selector=e.selector, label=e.label,
                grabbed=e.grabbed,
                enabled=e.enabled, width=e.width, height=e.height,
                group=getattr(e, "group", 0),
                pairing=getattr(e, "pairing", 0),
                readonly=bool(getattr(e, "readonly", False)))
        for e in getattr(shot, "elements", ())
        if getattr(e, "kind", "") and e.visible]
    return Surface(kind="page", controls=controls)


#: Where on a canvas to act. Never its centre, and never a fraction that
#: lands on a cell edge.
#:
#: The centre is a cell boundary for every even grid: 300 of 600 with twelve
#: columns is exactly 6.0 cells in, so a click there lands on a line and a page
#: whose cells toggle perfectly reads as one that ignored it. A build measured
#: by hand as correct at four cells had its own criterion recorded FAILED for
#: exactly that, and answered by adding a data attribute to the canvas "to
#: enable verification", which is instrumenting a correct program to satisfy
#: a broken measurement.
#:
#: Avoiding the centre is not enough on its own, which a test of this constant
#: caught after it had shipped: `0.36 x 25 = 9.0` lands **exactly** on an edge
#: on a 25-column grid, and `0.27 x 15 = 4.05` lands two pixels from one at 600
#: px. Searching every thousandth over the grids programs actually use (8, 10,
#: 12, 15, 16, 20 and 25 across) leaves only twenty fractions clearing them
#: all by a fifth of a cell, and they cluster around 0.22 and 0.78. So those
#: two are used as a 2x2 grid: spread across the canvas, and each coordinate
#: provably clear of every edge.
SAFE_LOW, SAFE_HIGH = 0.22, 0.78

#: The grids a generated program is actually built on. The constants above are
#: verified against this list rather than chosen to look plausible.
COMMON_GRIDS = (8, 10, 12, 15, 16, 20, 25)

#: Where a second stroke begins: the top-right corner, so it runs down and
#: *left* while the first runs down and right from `SAFE_LOW`. A stroke
#: retracing a line already on the canvas changes nothing, and a working
#: painter would look broken; crossing it once is enough to be sure the two
#: are different pixels.
SECOND_STROKE = (SAFE_HIGH, SAFE_LOW)

#: Where else to try the second stroke before saying a surface has stopped
#: drawing.
#:
#: **On a canvas where position decides the answer, one place is a sample.**
#: A palette holding three shapes takes a stroke on a shape and ignores one
#: on the background, which is the program working and is indistinguishable,
#: from a single trial, from a painter that draws in one corner and nowhere
#: else. Both answer the first stroke and refuse the second.
#:
#: So the second stroke is tried in several places and the surface is only
#: condemned if **none** of them draws. The painter whose backing store is a
#: quarter of its canvas still fails every one of these, because its whole
#: right-hand side is dead; the palette passes on the first stroke that finds
#: a shape. It is the same rule as the page-wide verdict standing down on an
#: incomplete surface: do not conclude from a thin sample.
SECOND_TRIES = ((SAFE_HIGH, SAFE_LOW), (0.5, 0.5), (SAFE_HIGH, SAFE_HIGH))

CANVAS_POINTS = ((SAFE_LOW, SAFE_LOW), (SAFE_HIGH, SAFE_LOW),
                 (SAFE_LOW, SAFE_HIGH), (SAFE_HIGH, SAFE_HIGH))


#: How many of a repeated control to exercise. A grid built from clickable
#: `<div>`s is 256 identical controls, and planning a case for each produced a
#: 505-case plan on one live build: hours of browser launches saying the
#: same thing 250 times. Three of a kind is enough to catch a control that
#: works only in one corner, which is the only way they differ.
SAMPLE_ALIKE = 3


def _sampled(controls: List[Control]) -> List[Control]:
    """Every distinct control, and at most `SAMPLE_ALIKE` of any repeated one.

    Alike means: same kind, same label, same size. Two buttons reading `Clear`
    and `Undo` are two controls however similar they look; 256 unlabelled cells
    of identical size are one control repeated.

    **Spread across the group, not the first few of it.** Taking the first
    three of nine identical cells is the top row of a noughts-and-crosses
    board, and a grid whose later rows are wired to nothing is a real fault
    in a generated program, and one this would never have reached.
    """
    # **A cell is not named.** Grouping on the label is right for buttons and
    # wrong for a board: memory cards take a label from their own `id`, so
    # every one of them counted as a distinct control and a sixteen-card
    # game planned twenty-one cases instead of three. What a cell is, is a
    # position, and whatever text it carries is the game being played.
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
        # The first two, because a board that alternates players needs a
        # second move to show it, then the rest spread to the far end.
        keep.update(where[:2])
        step = (len(where) - 1) / (SAMPLE_ALIKE - 2)
        keep.update(where[round(step * n)] for n in range(1, SAMPLE_ALIKE - 1))
    return [c for i, c in enumerate(controls) if i in keep]


def plan(surface: Surface, criteria: Sequence[Any] = ()) -> List[Case]:
    """Everything worth doing to this artefact, derived from what it has.

    The order is deliberate. The criteria come first because they are what the
    program owes; coverage follows, because a build that meets its contract and
    fails on its own buttons is still broken, and one that fails its contract
    is broken whatever else passes.

    Nothing here is a judgement. Each case says *do this, then something must
    have changed, which is the half a machine can settle. Whether what
    changed was the **right** thing is what the criteria are for, and what the
    investigator reads the numbers for.
    """
    # The criteria are not derived and do not belong here. What a program
    # owes is a judgement, and the acts that settle it have to be written by
    # something that has read both the criterion and the surface. See
    # `Pipeline._criteria_cases`, which asks for all of them in one turn and
    # hands them back as cases like any other. Passing them through here with
    # no acts made them run as an empty browser probe against a command-line
    # program, and every one came back *"the visible text is unchanged"*.
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

    # Opening it is a test. A page that throws on load has failed before
    # any control is reached, and three live builds shipped exactly that.
    add("open the page and let it settle", [], {"quiet": True})

    handles = [c for c in surface.operable if c.kind == "handle"]
    for c in _sampled(surface.operable):
        if c.kind in ("button", "link"):
            # `quiet`, because a derived case cannot know what a button
            # owes. Asserting *something must change* is a guess about
            # design, and a wrong guess is a false failure: a palette swatch
            # that sets the current colour and shows no selection border
            # changes nothing measurable and is not broken. Measured against
            # Claude Code's paint tool, which works and was hand-verified at
            # the pixel, that assertion produced **nine false failures out of
            # twenty-one cases**.
            #
            # What a button *owes* is what a criterion says, and criteria carry
            # their own expectations. What coverage is for is finding the
            # button that throws, or that cannot be pressed at all, and both
            # of those this still catches. The measurement is recorded either
            # way, so *"press Red → nothing changed"* is in front of the
            # investigator as a fact without being a verdict.
            add(f"press {c.name}", [{"click": c.selector}], {"quiet": True},
                c.selector)
            # Twice, because state machines break on the second press.
            # Undo after undo, start after start, a toggle that only toggles
            # one way. Nothing is asserted about *what* changes, only that
            # the program did not throw.
            add(f"press {c.name} twice",
                [{"click": c.selector}, {"click": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind in ("text", "number") and not c.readonly:
            # **A field is probed with values it can hold.** A number box
            # refuses letters at the browser level, so a case that types
            # `Sample item` into one performs no act at all, and a
            # temperature converter whose whole job is a number was never
            # once given a number. Two of the four variations were already
            # skipped for that reason and the third was left in, which is
            # the same bug with a shorter list.
            for label, value in TEXT_PROBES:
                if c.kind == "number":
                    if label in ("long", "awkward"):
                        continue
                    value = value and _typed_for(c)
                add(f"put {label} {'number' if c.kind == 'number' else 'text'} "
                    f"in {c.name}",
                    [{"fill": f"{c.selector}={value}"}], {"quiet": True},
                    c.selector)
        elif c.kind == "handle":
            # **A handle is dragged, and pressing it proves nothing.** A
            # split pane's bar and a row that reorders by dragging both do
            # exactly nothing when clicked, so a plan built only of clicks
            # exercised neither and then had nothing to say about either.
            if c.grabbed:
                # **`draggable` moves only through the HTML5 protocol**, and
                # it needs somewhere to land: a row dragged onto empty space
                # is a row put back where it was.
                #
                # And the landing place must be far from the row, not merely
                # a different one. Every reorder list here drops *before* the
                # target, so dropping a row onto the one directly below it
                # puts it exactly where it already was, the order line never
                # moves, and two working lists were reported as lists that
                # cannot be dragged. The far end of the list is a move by
                # any implementation.
                # The end furthest from this row, because a drop onto the
                # neighbour is a drop onto where the row already is, whether
                # the row happens to sit near the top or near the bottom.
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
                # **A bar that moves once and then cannot be caught again is
                # the commonest way for this to be broken**, and one drag
                # cannot tell that from a bar that works. The first drag is
                # the setup, so what is measured is only the second: bracket
                # both and the first one's success hides the second one's
                # failure, which is exactly how a frozen split pane passed.
                add(f"drag {c.name}, then drag it again",
                    [{"drag": c.selector}, {"drag": c.selector}],
                    {"changes": True, "second": True}, c.selector)

        elif c.kind == "range":
            # Quiet, for the reason a lone button is quiet: what a slider
            # owes is a judgement about the program. What this buys is that
            # the slider gets *moved*, which is what the whole-page verdict
            # needs to tell a dead page from one nobody touched.
            add(f"move {c.name}", [{"slide": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind in ("checkbox", "radio"):
            add(f"tick {c.name}", [{"click": c.selector}], {"quiet": True},
                c.selector)
        elif c.kind == "select":
            add(f"choose something in {c.name}", [{"click": c.selector}],
                {"quiet": True}, c.selector)

    # **A grid is pressed at a few places, never at all of them.** Cells are
    # interchangeable and there can be hundreds; a minesweeper field is a
    # hundred cases asking one question between them. `_sampled` is the same
    # rule the buttons go through, and cells are what it was described for.
    #
    # They are `quiet` cases for the reason a lone button is: what a cell
    # owes is a judgement about the game, and clicking a mine is supposed to
    # end it. What this buys is that the board gets *used*, which is what
    # `_nothing_responds` needs to be able to tell a dead page from one
    # nobody pressed.
    cells = [c for c in surface.controls if c.kind == "cell" and c.enabled]
    for c in _sampled(cells):
        add(f"click {c.name or c.selector}", [{"click": c.selector}],
            {"quiet": True}, c.selector)
        # **A cell is the one control that has to answer for itself**, and
        # only against its own other press. A button changes something else
        # by definition: pressing Add does not alter the Add button. A
        # square in a grid *is* the thing being operated, so a square that
        # answers the second click and not the first is one behind, whatever
        # the rest of the page did in the meantime.
        # Quiet, like the single click beside it: a flashcard's reverse
        # face is rotated away and cannot be clicked at all, and a cell the
        # driver could not reach is the page's business rather than a fault.
        add(f"click {c.name or c.selector} twice",
            [{"click": c.selector}, {"click": c.selector}],
            {"same_each": True, "itself": True, "quiet": True}, c.selector)
    if len(cells) > 1:
        add(f"click {cells[0].name or 'one cell'}, then the one beside it",
            [{"click": cells[0].selector}, {"click": cells[1].selector}],
            {"quiet": True}, cells[0].selector)

    # **A canvas is driven by whatever that program is driven by.** Asserting
    # that *clicking* one must change something is right for a paint tool and
    # nonsense for a game. Claude Code's snake works (arrow keys move the
    # centroid the right way for all four) and scored **1 of 5** here,
    # because four cases clicked a canvas that waits for a keypress and one of
    # them could not even be clicked through its start overlay.
    #
    # So the individual points only have to not throw, and **one** case asks
    # the question that is actually true of every interactive program: does
    # this canvas respond to *anything* a person can do to it. It still
    # catches `r5a_grid`, whose two handlers double-toggle so every click nets
    # to nothing and whose keys do nothing either.
    for c in surface.canvases:
        for i, (fx, fy) in enumerate(CANVAS_POINTS, 1):
            add(f"click {c.name} at point {i}",
                [{"click": f"{c.selector}@{fx},{fy}"}], {"quiet": True},
                c.selector)
        add(f"use {c.name}: click it, drag on it, and press the keys a "
            f"program like this is driven with",
            [{"click": f"{c.selector}@{CANVAS_POINTS[0][0]},{CANVAS_POINTS[0][1]}"},
             {"click": f"{c.selector}@{CANVAS_POINTS[3][0]},{CANVAS_POINTS[3][1]}"},
             {"press": "Space"}, {"wait": "0.4"},
             {"press": "ArrowRight"}, {"wait": "0.3"},
             {"press": "ArrowDown"}, {"wait": "0.3"},
             {"press": "Enter"}, {"wait": "0.4"},
             {"drag": c.selector}],
            # Asserted only where nothing else could have driven it. A
            # chart draws when you press Add, and a bouncing-balls canvas has
            # no balls until you add one: poking such a canvas proves
            # nothing, and demanding an answer from it called four working
            # programs dead. The rule this keeps is the old one: a canvas
            # nobody drew into is a finding only when the page offers nothing
            # else to press.
            ({"changes": True, "painted": True} if not surface.operable
             else {"quiet": True}), c.selector)

        # **A surface that took the first stroke has to take the second.**
        # One painter here draws a line and then silently ignores every
        # line after it, and nothing else in the plan can see that: the
        # whole-case comparison is satisfied by the first stroke, and the
        # second is lost inside it.
        #
        # It asks nothing of a canvas that is not drawn on. Whether this is
        # a drawing surface or a chart is not guessed at and not read off
        # the buttons around it. **The first stroke settles it**, and a
        # chart, which draws for nobody, exempts itself by not answering.
        # That is the same move the settle rule makes: take the baseline
        # from the program's own behaviour rather than from a policy about
        # what kind of program it is.
        add(f"draw on {c.name}, then draw somewhere else on it",
            [{"drag": f"{c.selector}@{SAFE_LOW},{SAFE_LOW}"}]
            + [{"drag": f"{c.selector}@{x},{y}"} for x, y in SECOND_TRIES],
            {"again": True}, c.selector)

        # **A control that answers only its second press has lost one.** The
        # two presses are identical and each starts from a state that was
        # measured, so a page where the first does nothing and the second
        # does something is not describing a toggle or an inert button. It
        # is one behind. Two painters here undo nothing on the first press
        # and one stroke on the second.
        #
        # The rule is about any control. The *scope* is a page with
        # something drawn on it, because pressing from a page that has just
        # loaded is not a fair question: a control with nothing to act on is
        # correctly inert, and this is the first state the plan reaches
        # where one has something to be wrong about.
        #
        # **Two strokes, not one.** A history that is one behind restores
        # the state it is already in, so with a single stroke on the stack
        # both presses are inert and the fault is invisible. It takes two
        # for the second press to land on something the first should have.
        for b in surface.operable:
            if b.kind not in ("button", "link"):
                continue
            add(f"draw on {c.name} twice, then press {b.name} twice",
                [{"drag": f"{c.selector}@{SAFE_LOW},{SAFE_LOW}"},
                 {"drag": f"{c.selector}@{SECOND_STROKE[0]},{SECOND_STROKE[1]}"},
                 {"click": b.selector}, {"click": b.selector}],
                {"same_each": True}, b.selector)

    # A field and the button beside it are one gesture, and separately they
    # test nothing. Typing into a box and never submitting exercises no
    # handler; pressing Add with an empty box is the empty case.
    #
    # **Beside it** is the whole difficulty, and pairing the first field with
    # every button got it wrong. A kanban board with three columns has three
    # "New card…" boxes and three "+" buttons; filling the first column's box
    # and pressing the third column's button does nothing, correctly, and the
    # case then reported a working board as broken. So the pairing follows
    # the widget each control is in, and a field is paired with buttons
    # outside its own widget only when there is nowhere else to look.
    # A readonly box is an *output*: a password generator writes its answer
    # into one. Typing into it and then demanding the button respond asks the
    # program to react to something it never accepts, and a working generator
    # failed on exactly that: the case typed into the display and pressed
    # Copy.
    fields = [c for c in surface.operable
              if c.kind in ("text", "number") and not c.readonly]
    buttons = [c for c in surface.operable if c.kind == "button"]
    if fields and buttons:
        order = {c.selector: i for i, c in enumerate(surface.controls)}

        def nearest(field: Control, choices: List[Control]) -> List[Control]:
            """The button a person would press after typing in this box.

            Not every button on the widget. A todo list has Add beside the
            field and All, Active, Done and Clear completed further along,
            and pairing the box with those asserts that typing a task and
            pressing a *filter* must change something, which it must not,
            and three working lists were reported broken for behaving
            correctly. The one that follows the field is the one that takes
            it; the rest are its neighbours, not its partner.
            """
            at = order.get(field.selector, 0)
            # Same form, or same container. That is what makes them a pair;
            # merely being the next button on the page does not.
            with_it = [b for b in choices
                       if not (b.pairing and field.pairing)
                       or b.pairing == field.pairing]
            after = sorted((b for b in with_it if order.get(b.selector, 0) > at),
                           key=lambda b: order.get(b.selector, 0))
            # Nothing after it is not a reason to reach backwards. One todo
            # list here has no Add button at all: a task is submitted by
            # pressing Enter, and the only button on the page is *Clear
            # completed*, which correctly ignores what was typed. Pairing
            # with whatever is nearest makes a case out of two unrelated
            # controls. Losing the case is honest; failing the program is
            # not.
            return after[:1]

        for field in fields[:3]:
            near = [b for b in buttons if b.group and b.group == field.group]
            alone = len(fields) == 1 and not near
            for b in nearest(field, near or (buttons if alone else [])):
                # This one keeps `changes`: typing and submitting is the whole
                # gesture a form exists for, and a page that answers it with
                # nothing measurable has not accepted the input.
                # `changes` for content, not for a setting, and which one a
                # number box is depends on what the program is. A Celsius
                # field is content: type into it and a converter that
                # converts nothing is broken. A brush size is a setting:
                # choose one, press Clear on an empty canvas, and a working
                # drawing tool does nothing at all, which was reported as a
                # fault. What separates them is the canvas. A program with
                # one is judged by what happens on it, which is what the
                # drag case is for, and the boxes around it are knobs for
                # it. A program without one has nowhere else to answer.
                setting = field.kind != "text" and bool(surface.canvases)
                expect = {"quiet": True} if setting else {"changes": True}
                # **Fill every field of the widget, not just this one.** A
                # sign-up form refuses to advance while the password is
                # empty, and it is right to: filling one box and demanding
                # the button respond asserts the program should accept a
                # half-finished form. So the whole widget is filled and the
                # case is named for the field it is about.
                fills = [{"fill": f"{other.selector}={_typed_for(other)}"}
                         for other in fields
                         if other.group == field.group or other is field]
                add(f"type into {field.name} then press {b.name}",
                    fills + [{"click": b.selector}], expect, b.selector)

    # Two buttons in each order. Undo before Clear and Clear before Undo
    # are different programs, and a generated one routinely gets one of them
    # wrong. Capped, because this is the term that grows fastest.
    for a in buttons[:3]:
        for b in buttons[:3]:
            if a.selector == b.selector:
                continue
            add(f"press {a.name}, then {b.name}",
                [{"click": a.selector}, {"click": b.selector}], {"quiet": True})
    return cases


#: What a case may ask for, and it is exactly what `browser.perform` can do.
#: An act naming anything else is dropped rather than performed, so a verb
#: listed here that the driver cannot carry out is worse than a missing one:
#: the case runs, asserts against a page nothing was done to, and reports on
#: it. `run` was here for command-line programs and outlived them.
ACT_VERBS = ("click", "dblclick", "press", "fill", "wait", "drag")


def as_acts(raw: Any) -> List[Dict[str, str]]:
    """A reply's `acts` as pairs the runner understands.

    Tolerant about shape and strict about verbs: an act that is not one of
    these is dropped rather than guessed at, because performing something
    nobody asked for is worse than performing nothing.
    """
    out: List[Dict[str, str]] = []
    for step in raw if isinstance(raw, list) else []:
        if isinstance(step, str):
            verb, _, arg = step.partition(" ")
            step = {verb.strip(): arg.strip()}
        if not isinstance(step, dict):
            continue
        for verb, arg in step.items():
            if str(verb) in ACT_VERBS and str(arg).strip():
                out.append({str(verb): str(arg).strip()})
    return out
