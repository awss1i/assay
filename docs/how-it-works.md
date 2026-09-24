# How It Works

*What assay measures, what it drives, and what it will and will not claim.
Linked from the [README](../README.md).*

These are in the order they happen, down to the last two, which are not
steps at all. Every rule is enforced against the
[benchmark](../bench/README.md), and where a number is quoted it is the
measurement that set the rule.

## Contents

- [It serves the folder and never builds it](#it-serves-the-folder-and-never-builds-it)
- [It waits until the page stops arriving](#it-waits-until-the-page-stops-arriving)
- [It measures the surface](#it-measures-the-surface)
- [It derives a plan](#it-derives-a-plan)
- [It carries the plan out, and measures](#it-carries-the-plan-out-and-measures)
- [It lets a moving canvas come to rest](#it-lets-a-moving-canvas-come-to-rest)
- [It reports pass, fail, or could not tell](#it-reports-pass-fail-or-could-not-tell)
- [What it will not claim](#what-it-will-not-claim)
- [What it will claim, without an opinion about design](#what-it-will-claim-without-an-opinion-about-design)

## It serves the folder and never builds it

The page is served over loopback rather than opened off the disk, because a
`file://` origin blocks every module the page loads.

What it will not do is run your build. `npm install` executes whatever the
dependency tree asks for, as whoever typed the command, and this is a tool for
checking code nobody has read. Point it at a source tree and it says so:

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser cannot run. This is a source tree, not a built one.
  Build it first, in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay will not run that for you: installing dependencies executes their setup scripts, and this is a tool for checking code nobody has read.
```

## It waits until the page stops arriving

`load` fires before a framework has rendered anything, so a fixed pause
measures whatever happened to be on screen at that moment.

Nothing is waited *for*. What is watched is whether the set of controls is
still changing, and the page is ready once that set holds still.

With one qualification, which is the whole difficulty: **a page can be
perfectly still and not be finished**, because a spinner does not move. So
quiet counts as readiness only once there is something on the page to work.
Without that, a page showing *Loading…* offers no controls, plans a single
case asserting that nothing threw, and an empty page throws nothing, so
working apps came back `1 case, 1 passed`.

## It measures the surface

Every button, field, select, canvas and link the page renders, each with a CSS
selector naming exactly one element, plus its label, whether it is enabled,
its size, and which widget it belongs to.

**From the rendered page, never the markup.** A control built at run time is
as real as one written into the HTML, and one the CSS hides with
`display: none`, `visibility: hidden` or `opacity: 0`, or shrinks to nothing,
is not there at all.

It also counts things no tag announces:

| | how it is recognised |
|---|---|
| a cell in a grid of plain divs | `cursor: pointer`, the page saying *click this* |
| a sortable table header | the same, on a `th` |
| an editable region | `contenteditable`, a text box without the tag |
| a drag handle or resize bar | `col-resize`, `move`, `grab`, `draggable` |

A click handler attached in JavaScript cannot be read from the DOM, so the
cursor is the only thing that says an element does something.

## It derives a plan

- Press every control, and press it twice, because state machines break on the
  second press.
- Put empty, ordinary, very long and awkward text in every field, and numbers
  in fields that only take numbers.
- Click a canvas at four points chosen to clear the cell boundaries of every
  common grid, drag across it, and drive it with the keyboard.
- Draw on it a second time, somewhere the first stroke did not reach.
- Drag every handle, and drag it twice, because a bar that moves once and then
  cannot be caught again is the commonest way for one to break.
- Drag a `draggable` row onto the far end of its list, through the HTML5 drag
  protocol, because mouse events never raise `dragstart`.
- Move every slider to the far end of its range, tick every box and radio,
  and choose something in every select.
- Type into a field and submit it with the button beside it.
- Fill a list in and submit it twice before pressing the controls its rows
  bring, such as Delete, because a Delete that removes the wrong row cannot
  show that with one row on screen.
- Press each pair of buttons in both orders.

## It carries the plan out, and measures

In a fresh tab per case, before and after: painted pixels per canvas, their
centroid, their mean colour, an exact pixel hash, the visible text, what is
in the fields (including whether each box is ticked), the element count, and
a hash over every element's style and class.

A 3D canvas is read through a frame callback, because a WebGL drawing buffer
is already empty by the time anything else can look at it.

It answers what the page asks, as well. A board wanting a card title through a
dialog gets one, because dismissing is not the neutral choice it looks like:
it answers *no* to everything, which is exactly the answer that makes a
feature not happen.

## It lets a moving canvas come to rest

A game that plays itself moves during a case whatever is pressed, so movement
proves nothing. A program still producing frames when the wait is over is
plainly alive and is asked nothing further. One that has gone quiet is a
program where whatever happens next is down to what was done to it.

## It reports pass, fail, or could not tell

The third never reads as failure, because recording a check that did not
happen as one that failed sends you after a bug that is not there. One
generated calculator declares `function eval()`, replacing the global the
driver measures through, so every reading comes back empty. That page is
reported as unreadable, not as blank, and the program works.

## What it will not claim

**A derived case cannot know what a control owes.** Asserting that pressing a
button must change something is a guess about design: a palette swatch that
sets the current colour and shows no selection border changes nothing
measurable and is not broken. So a button only has to survive being pressed.

What a control owes is what an acceptance criterion says, and assay takes
those too: you pass them in with the acts that check them.

Four things also stand a finding down, because each is the page explaining
itself:

- **A control the program disabled.** `disabled` is the page saying *not now*,
  and a limit that is not taken at its word is not a limit.
- **Surface it could not reach.** A page-wide verdict drawn from a plan that
  missed the only part that works is a verdict about the plan.
- **A sequence that answered and went back.** Select then deselect ends where
  it started, and that is two answers, not none.
- **A program that ran to a stop on its own.** It reached a state it chose,
  unless it printed what to press and then ignored it.

## What it will claim, without an opinion about design

These are the cases where a program contradicts itself, which needs no view
about what it was for.

**A surface that took the first stroke has to take the second.** Whether a
canvas is something you draw on or a chart you only look at is not guessed at.
The first stroke settles it, and a chart, which draws for nobody, exempts
itself by not answering. The second stroke is tried in several places, because
on a canvas where position decides the answer one place is a sample.

**A control that does nothing on its first press and something on its second,
from the same state, is one behind.** Both presses are the same act and the
state before each was measured. That is what an undo stack does when it stores
the picture after the change instead of before it. Nothing here reads the word
on the button.

**A page that answers none of its own controls has nothing behind it.** The
permission a swatch gets is that what it stores is read by something else, so
when nothing ever changes whatever is pressed, nothing is reading it.
Deliberately the hardest to trigger: it needs a page that offered something to
press, cases that pressed it, nothing observed changing anywhere, and no
interactive surface the plan failed to reach.

**A page that says what to press and then ignores it** has broken a contract
it wrote itself, and that is the one thing separating a program that finished
from a program that is stuck.

**A control that goes back has to take the page with it.** A tag pressed a
second time that returns to how it looked before is saying its filter is off
again, and a list still filtered contradicts it. Both halves are the page's
own: the control's appearance, and whether the page is where it started.

**Of two controls that reverse each other, both have to answer.** The pair is
read from the page's own labels: two whose words differ by exactly one, and
that one a genuine opposite, such as Next and Previous or Undo and Redo. If
one changes the page every time it is pressed and the other never does, even
straight after its partner, the silent one is reported.

**A row that goes has to be the one pressed.** With two different rows on
screen, pressing Remove on one and watching the other disappear is the wrong
row gone. Two rows that read the same are left alone, because they cannot say
which of them went.

**What goes into a list has to come out in it.** A value typed in and
accepted into a list has to appear in the row it made. This is asked of lists
only: a sign-up form is allowed to take a password and show nothing.

**A number that counts a list has to read zero when the list is empty.** A
number that moves by one every time a row comes or goes is counting the list,
and it cannot be anything but zero when there is nothing to count. Being off
by a constant is not enough on its own, because a flat fee moves in step with
a basket and is right. Whole numbers only.

**A number that follows a list has to follow it both ways.** A total that
moves every time a row is added and never when one is removed is still
showing a figure for rows that are gone.

**Nothing on the page reads `NaN`, `undefined` or `[object Object]`.** In
the text or in the fields, each is a value read before it was set or worked
out from something that was not a number. The one exception is a case that
typed words into a box, where `NaN` can be the page answering correctly.

**Every control is wired to something that is there.** Two choices in one
radio group carrying the same value, a label pointing at an id the page does
not have, and two labels pointing at the same control are all read straight
from the markup.

**A box has to accept the example it shows.** A field whose own placeholder
fails its own `pattern` is a form nobody can finish.

**A canvas has to show something by the end.** Asked once the whole plan has
run, with every control pressed and every field filled, and only when there
is no surface the plan failed to reach.

**And a page that throws has stopped.** An uncaught exception is reported
with its message, because everything after it did not happen.
