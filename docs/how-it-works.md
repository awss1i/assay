<h1 align="center">How It Works</h1>

---

<p align="center">assay opens your page in a real browser, finds every control on it, uses each
one in a planned set of checks, and compares the page before and after every
check. It doesn't know what your page is for, so it only reports something
when the page contradicts itself: it throws an error, a control reacts one
press late, a count says 1 when the list is empty, and so on.</p>

<p align="center">The first half of this page describes how a run goes. The second half goes
through each kind of check: what assay does, what it reports and the exact
message it prints, and when it deliberately stays quiet and why. Every rule
here is measured against the <a href="../bench/README.md">benchmarks</a>, and most of the
exceptions exist because a broader version of the rule flagged a page that
works.</p>

---

## Contents

- [How a run goes](#how-a-run-goes)
  - [Serving the page](#serving-the-page)
  - [Waiting for the page to load](#waiting-for-the-page-to-load)
  - [Finding the controls](#finding-the-controls)
  - [Planning the checks](#planning-the-checks)
  - [Running each check](#running-each-check)
  - [Passed, failed, or not checked](#passed-failed-or-not-checked)
  - [Grouping findings](#grouping-findings)
- [What assay checks](#what-assay-checks)
  - [Opening the page](#opening-the-page)
  - [Pressing buttons and links](#pressing-buttons-and-links)
  - [Typing into fields](#typing-into-fields)
  - [Filling in a form and submitting it](#filling-in-a-form-and-submitting-it)
  - [Adding items to a list and removing them](#adding-items-to-a-list-and-removing-them)
  - [Numbers that count or total a list](#numbers-that-count-or-total-a-list)
  - [Saving and reloading](#saving-and-reloading)
  - [Clicking cells, chips and cards twice](#clicking-cells-chips-and-cards-twice)
  - [Buttons that come in opposite pairs](#buttons-that-come-in-opposite-pairs)
  - [Drawing on a canvas](#drawing-on-a-canvas)
  - [Pressing a button after drawing](#pressing-a-button-after-drawing)
  - [Games and animated canvases](#games-and-animated-canvases)
  - [Dragging handles and rows](#dragging-handles-and-rows)
  - [Sliders, checkboxes, dropdowns, colours and files](#sliders-checkboxes-dropdowns-colours-and-files)
  - [Tabs and expandable sections](#tabs-and-expandable-sections)
  - [Labels and radio buttons in the markup](#labels-and-radio-buttons-in-the-markup)
  - [Fields whose placeholder fails their own pattern](#fields-whose-placeholder-fails-their-own-pattern)
  - [NaN, undefined and [object Object] on the page](#nan-undefined-and-object-object-on-the-page)
  - [A page where nothing responds](#a-page-where-nothing-responds)
- [What assay can't check](#what-assay-cant-check)

---

## How a run goes

### Serving the page

assay serves the folder on localhost instead of opening the file directly,
because pages opened from `file://` can't load JavaScript modules.

It never runs your build. `npm install` runs whatever scripts your
dependencies contain, and assay is meant for code nobody has reviewed yet. If
you point it at a source tree, it tells you what to run yourself:

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser cannot run. This is a source tree, not a built one.
  Build it first, in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay will not run that for you, because installing dependencies executes their setup scripts, and this is a tool for checking code nobody has read.
```

### Waiting for the page to load

The `load` event fires before most frameworks have drawn anything, so assay
uses neither it nor a fixed delay. It waits until the page's controls stop
changing.

A page showing only a spinner is also still, so stillness only counts as
ready once the page has something to interact with. Otherwise a page stuck on
*Loading…* would look like a finished page with no controls.

### Finding the controls

assay lists every button, field, dropdown, canvas and link the browser
renders, each with a CSS selector, its label, whether it's enabled, its size,
and the form or container it belongs to.

It reads the rendered page, not the HTML source. A control created by
JavaScript counts, and one hidden with `display: none`, `visibility: hidden`,
`opacity: 0` or a zero size doesn't.

It also finds controls that no HTML tag announces:

| control | how assay recognises it |
|---|---|
| a cell in a grid made of plain divs | `cursor: pointer` |
| a sortable table header | `cursor: pointer` on a `th` |
| an editable region | `contenteditable` |
| a drag handle or resize bar | `col-resize`, `move`, `grab`, or `draggable` |
| a star or switch drawn over a hidden box | a visible `label` whose radio button or checkbox is hidden |

Click handlers added in JavaScript can't be read from the page, so the mouse
cursor is often the only sign that an element does something.

### Planning the checks

From the controls it found, assay builds a list of checks. Each check is one
or more actions, like pressing a button twice, or filling in a form and
pressing the button that sends it. The second half of this page describes
every kind of check.

When a page has many controls that look alike (the same kind, label and
size, like the cells of a grid), assay uses at most three of them, spread
across the group rather than the first three. One page with a 256-cell grid
produced a 505-check plan before this, and all the extra checks said the same
thing.

### Running each check

Each check runs in a fresh tab, starting from a page that has just loaded.
Before and after the check, assay records:

- each canvas's painted pixels, their centre, their average colour and an
  exact pixel hash,
- the visible text,
- every field's contents and whether each box is ticked,
- the number of elements on the page,
- a hash of every element's style and class.

WebGL canvases are read inside an animation frame, because their contents are
already cleared by the time anything else could read them.

An `alert` counts as the page responding. An alert saying *Length must be
mm:ss* is a form correctly refusing bad input, even though nothing else on the
page changed. A `prompt` or `confirm` is the page asking a question, so it
doesn't count as a response by itself. What the page does with the answer
does. assay answers prompts with a sensible value and accepts confirms rather
than dismissing them, because dismissing would cancel the feature being
tested.

### Passed, failed, or not checked

A check fails when one of the rules below is broken. Otherwise it passes. A
check that couldn't be carried out at all is reported as *not checked*, never
as a failure.

For example, one generated calculator defines its own `eval` function, which
breaks the way assay reads the page. assay reports:

```
assay could not read this page, because the page replaces a built-in function that assay relies on (such as `eval` or `Function`). This says nothing about whether the page works
```

That page is reported as not checked, and the calculator does work.

If the page refuses one action in a check (for example, a canvas hidden
behind a *Press Space to start* overlay can't be clicked), the rest of the
check goes ahead. The check only fails for this when none of its actions
could be done, and the message starts with *could not*.

A disabled control is the page saying "not now". assay records that the
control was disabled and doesn't count its silence against the page. A
quantity box that clamps 25 to its maximum of 10 and disables `+` is working
as intended.

### Grouping findings

When one bug fails several checks, the first failure shows the message and
the rest point back to it:

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page did not change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

and the summary line says how many are repeats:

```
18 case(s) planned, 18 carried out, 10 passed, 8 failed (7 of them repeat an earlier finding)
```

Every failure is still listed and counted, and the exit code doesn't change.
Grouping only changes how the output reads.

Two failures are grouped only when both of these are true:

- They broke the same rule with the same message, apart from names quoted in
  it.
- They happened on the same kind of control in the same place, like the chips
  of one tag bar or the cells of one grid. Controls with names, like buttons,
  also need the same name, so Undo and Redo are never grouped.

Crashes are grouped only when they have the same error message and were
thrown from the same line of code.

If every check ran on a page that had already thrown an error while loading,
a finding about the whole page (such as nothing responding) says so:

```
    ↳ the page threw an error while loading (C001), before anything was pressed
```

Every grouping on the benchmark pages is checked against a hand-written
answer key, [`bench/links.txt`](../bench/links.txt).

---

## What assay checks

Each section below starts with what assay does to the page, then what it
reports, then when it stays quiet and why. Findings about a single check are
numbered `C001`, `C002` and so on. Findings about the whole run, which no
single check could show, are numbered `F001`, `F002`, and the two page-wide
findings (nothing responds, nothing is drawn) are `C000`.

### Opening the page

The first check opens the page and waits for it to settle, without pressing
anything.

If the page throws an uncaught error, on load or during any later check,
assay reports it with the browser's own error message:

```
C001 [FAILED] open the page and let it settle
    → the page threw an error and stopped running, Cannot read properties of null (reading 'addEventListener')
```

Every check that ran into the same error reports it, and the repeats are
grouped under the first one.

If the page shows nothing at all, assay reports:

```
    → the page shows nothing at all (no text, no images and nothing drawn), so there is nothing to test
```

This was added for a React app whose component returned `null`: it offered
no controls, so the only check was "open the page", and that passed. A blank
page is only reported when it offers nothing to use, or when a check that
expects a response (like submitting a form) leaves it blank. A drawing tool
that is just an empty canvas until you draw on it isn't reported for being
blank on load.

### Pressing buttons and links

assay presses every button and link once, and then twice in a row, because
state bugs often show on the second press: a second Start, an Undo after
Undo, a toggle that only toggles one way. It also presses the first three
buttons in pairs, in both orders (Undo then Clear, and Clear then Undo),
because a page can get one order right and the other wrong.

For these checks, assay only reports an error the page threw. It doesn't
require a button to change anything, because it can't know what the button
is for. A colour swatch that sets the brush colour without showing a
selection changes nothing visible, and it isn't broken. When an earlier
version required a visible change, it flagged 9 of 21 checks on a paint
tool that worked. What happened is still recorded in the evidence ("the
visible text is unchanged", and so on), just not as a failure.

A button that never does anything is still caught in two ways: when it has
an opposite that does work (see
[opposite pairs](#buttons-that-come-in-opposite-pairs)), and when nothing on
the whole page responds (see
[a page where nothing responds](#a-page-where-nothing-responds)).

### Typing into fields

assay types four kinds of value into every text field: nothing, ordinary
text (`Sample item`), a 300-character string, and text with commas, quotes
and HTML in it. Number fields get nothing and a number. Date and time fields
(`date`, `time`, `datetime-local`, `month` and `week`) get nothing and a valid
value for their type. After typing, assay leaves the field, so pages that
react to the `change` event see it.

For these checks, assay only reports an error the page threw. Read-only
fields are never typed into, because they're outputs. A password generator
writes its answer into one.

### Filling in a form and submitting it

For each field that has a button after it in the same form or container,
assay fills in every field in that form, then presses the button. Before
pressing, it also picks the first option in each set of radio buttons in the
form and changes each dropdown, because a form that requires a rating or a
group is right to refuse to send without one.

Each field gets a value its type accepts: an email address in an email
field, a phone number in a `tel` field, a URL in a `url` field, a valid date
in a date field. Only then is the label considered, so a text field labelled
*Phone* gets `555-0100` and one whose placeholder says *mm:ss* gets `3:30`.

This is the one kind of check where assay requires something to change. A
page that takes what was typed, has its submit button pressed, and shows no
change anywhere hasn't accepted the input:

```
C007 [FAILED] type into Title then press Add
    → nothing on the page changed at all
```

assay doesn't report this when:

- **The button isn't the field's own.** Only the first button after the field
  in the same form or container is pressed. A todo list's filter buttons
  (All, Active, Done) correctly ignore what was typed, and pairing the field
  with them flagged three working lists. A field with no button after it,
  like a todo list that adds on Enter, gets no submit check at all.
- **The field is a setting on a canvas page.** On a page with a canvas, a
  number or date field is usually a setting like brush size, so the page
  isn't required to respond, and the canvas checks judge it instead.
- **The page answered with an alert,** such as a form refusing bad input.
- **The button is disabled.**
- **The page has stopped by itself,** like a game that has ended, unless the
  page said what to press (see [games](#games-and-animated-canvases)).

### Adding items to a list and removing them

A to-do list on load is only a box and a button. The checkbox, the Delete
button beside each item and the count of what's left don't exist until an
item does. So when a page has a form, assay fills it in and submits it twice,
with different values the second time, and then plans checks for every
control that appeared. Each of those checks starts by adding the same two
items, so its name ends in *with two saved*. Two different items are needed
because a Delete that removes the wrong item can't show that when there is
only one.

When a check removes an item but the item it was pressed on is still there,
assay reports:

```
C014 [FAILED] press Remove, with two saved
    → this removed a row, but not the one it belongs to, and 'Another item https://example.com/other' is still there
```

Items with identical text are skipped, since they can't show which one went.

At the end of the run, assay also checks that what was typed into the form
shows up in the item it created. If some of the typed values are missing,
it reports:

```
F001 [FAILED] values typed into a list show up in the new row
    → 'https://example.com/page' was typed in and accepted, but the new row in the list does not show it, first seen at C009
```

This is only asked of a list, meaning anything whose count changed during the
run, including the rows of a plain table. It's checked with two items in the
list, because with one item a running total equals the amount typed and a
row showing the total would look correct. assay doesn't report it when:

- **The form isn't a list.** A sign-up form that says *Account created* and
  shows neither the email nor the password is correct, and required to hide
  the password.
- **None of the typed values appear.** A row that shows none of what was
  entered is a list showing something else entirely, not one field going
  missing.
- **The page refused the second item.** A value the page didn't accept isn't
  counted as lost.

### Numbers that count or total a list

Throughout the run, assay reads every number on the page along with how many
items the list holds, and compares them at the end.

A number that goes up and down by one with the list is counting it, so it
has to read zero when the list is empty. If it doesn't, assay reports:

```
F002 [FAILED] the count of items matches the list
    → a number on this page goes up and down by one with the list, so it counts the list, but it shows 1 when the list is empty. It is +1 off at every size
```

It needs at least three readings at two or more list sizes, and it only uses
whole numbers, since a decimal is a measurement or an amount of money, not a
count. Being off by a fixed amount isn't reported by itself. A basket that
adds a flat delivery fee moves in step with its contents and is correct at
every size. Only a count that isn't zero on an empty list is reported.

A number that changes every time an item is added is following the list, so
it should also change when one is removed. If it never does, assay reports:

```
F003 [FAILED] a total that follows the list also goes down
    → a number on this page changed every time the list grew (4 times) but never when it shrank (2 times), so it stops following the list when items are removed
```

This is the expense tracker that forgets to recalculate its total when a row
is deleted. Amounts of money are allowed here, because a running total is
the most common number that should follow a list. The list must have been
seen both growing and shrinking, and the number must have changed on every
single addition, since a number that only sometimes moves is tracking
something else.

### Saving and reloading

After adding two items, assay checks whether the page wrote them to its own
`localStorage` or `sessionStorage`. If it did, the page is promising they'll
be there next time, so assay adds the two items again, reloads the page, and
checks they're still shown. If they're gone, it reports:

```
C021 [FAILED] save two, reload, and they are still there
    → 'Sample item' and 'Another item' were saved in browser storage by the page, but are gone after reloading it
```

It's only asked when the page both saved the values and was showing them
before the reload. A page that never saves anything is never asked.

### Clicking cells, chips and cards twice

Clickable elements that aren't buttons (grid cells, tag chips, cards, stars)
are clicked once, then twice in a row, and the first one is also clicked
followed by the one beside it. For the double click, assay watches the
element itself as well as the rest of the page, because the element is the
thing being operated.

If the element didn't change on the first click and did on the second, it's
reacting one click late, and assay reports:

```
C011 [FAILED] click Mon 9:00 twice
    → clicking this twice, the first click did not change it and the second did, so it reacts one press late
```

This caught a scheduler whose booked styling was inverted. The element must
have changed on the second click itself, not just the page around it. A key
on an on-screen keyboard never changes its own appearance (each press types a
letter onto a board elsewhere), and reading the board changing as the key
changing flagged every key as late.

If the element changed on the first click and changed back on the second,
but the rest of the page didn't change back, assay reports:

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page did not change back, so what the first click did is still in effect
```

This is a tag filter whose tag looks switched off again while the list stays
filtered. It's only reported when the second click changed nothing outside
the element except the element itself. A tree folder that closes its inner
folders when it closes redraws its children and its row count on the second
click, which is the page deliberately choosing a tidy state, so it isn't
reported. An element that looks the same after both clicks, like a thumbnail
that opens a lightbox, isn't reported either.

These clicks are otherwise judged like button presses. Only errors are
reported.

### Buttons that come in opposite pairs

A lone button is allowed to do nothing visible. What a page can't explain is
offering two buttons that reverse each other, where one changes the page
every time and the other never does.

assay finds pairs by their labels. Two labels that differ by exactly one
word, where that word is an opposite (next and previous, forward and back,
undo and redo, up and down, increase and decrease, more and less, plus and
minus, add and remove or delete, expand and collapse). assay also presses
buttons in pairs, in both orders, so the silent one is pressed straight after
its partner, when it has something to reverse. If one changed the page every
time and the other never did, assay reports:

```
F001 [FAILED] Previous works as well as Next
    → Next changed the page every time it was pressed, but Previous never did, even right after Next. As a pair, Previous should reverse what Next does
```

Previous on a freshly loaded deck correctly does nothing, which is why the
press that counts is the one straight after Next.

### Drawing on a canvas

For every canvas, assay:

- clicks it at four points, chosen to avoid the edges of cells on common grid
  sizes,
- uses it the way a program like it is driven: two clicks, then Space, the
  right and down arrows, Enter, and a drag,
- draws a line on it, then draws another line somewhere else.

If the first line appeared and the second didn't, the canvas has stopped
accepting drawing, and assay reports:

```
C019 [FAILED] draw on canvas, then draw somewhere else on it
    → the first line drawn on this canvas appeared, but a second line drawn elsewhere did not, so the canvas stopped accepting drawing
```

The second line is tried in several places before this is reported. A canvas
that ignored the first line isn't asked at all. A chart doesn't draw when you
drag on it, and it exempts itself by not responding. This caught a painter
that draws one line and silently ignores every line after it, which nothing
else in the plan could see.

Clicks on a canvas are only required to change it when the page offers
nothing else to use. A chart draws when you press Add, and a canvas of
bouncing balls is empty until you add a ball, so requiring a response from
the canvas itself flagged four working pages. On a page that is only a
canvas, if using it doesn't change the canvas, assay reports:

```
    → the canvas this check clicked did not change, even if other parts of the page did
```

and if the canvas still shows nothing afterwards:

```
    → 1 canvas(es) still show nothing after every step of this check
```

At the end of the run, if no canvas ever showed anything but a single flat
colour, assay reports it for the whole page:

```
C000 [FAILED] something appears on the canvas
    → nothing ever appeared on this canvas, 12 checks used the page and the canvas stayed one flat colour, so whatever the program draws is not reaching the screen
```

This caught three WebGL cubes whose transform clipped every vertex away. The
canvas measured as completely painted, in one colour, with nothing on it.
It's only reported when at least two checks used the page, no other check
failed, and every control on the page was reached, since a control assay
couldn't reach might be the one that starts the drawing.

### Pressing a button after drawing

For every button on a page with a canvas, assay draws two lines, then presses
the button twice. Both presses start from a state it measured, so if the
first press did nothing and the second did something, the button is one
press behind:

```
C016 [FAILED] draw on canvas twice, then press Undo twice
    → pressing this twice from the same starting point, the first press changed nothing and the second did, so it reacts one press late
```

This is what an undo history that saves the state after each change, instead
of before it, looks like. The first Undo restores the picture that is already
on screen. It takes two lines, because with only one line on the history both
presses do nothing and the fault is invisible. It's asked after drawing
rather than on a freshly loaded page, because a control with nothing to act
on is correctly inert.

If the second line didn't draw anything, the check passes instead, and its
evidence says:

```
the second line drew nothing, so there was no second step to undo
```

A correct Undo spends its first press on that empty step, which isn't being
one behind. This is how a working paint tool, whose second stroke didn't
draw, was previously reported as having a late Undo. The canvas itself is
still reported if the second line didn't draw (see
[drawing on a canvas](#drawing-on-a-canvas)).

### Games and animated canvases

If a canvas animates by itself, like a game that plays on its own, assay
waits for it to stop before acting. If it never stops, changes on the canvas
can't be credited to anything assay did, so those checks don't require a
change.

A program that has stopped by itself, like a snake game that hit a wall,
isn't reported for ignoring what was pressed afterwards. That's the game
working. The exception is a page that says what to press. If it shows
*Press Space to restart* and pressing Space changes nothing, the page has
broken its own instruction, and assay reports:

```
    → the page says to press Space, but pressing Space changes nothing
```

A finished game with no restart can still look broken, which is listed in
the README's limits.

### Dragging handles and rows

A split pane's divider and a row that reorders by dragging do nothing when
clicked, so assay drags them:

- Each drag handle (`col-resize`, `move` or `grab` cursor) is dragged, and in
  a second check dragged twice. In the second check only the second drag is
  measured, because a divider that moves once and then can't be caught again
  is the most common way for it to be broken, and measuring both drags
  together lets the first one hide the second.
- Each `draggable` row is dragged onto the far end of its list, using real
  HTML5 drag events. The far end, because most lists drop a row before the
  target, so dropping a row onto its neighbour puts it back where it was and
  looked like a list that can't be dragged.

A drag is expected to change the page. If it doesn't, assay reports:

```
C012 [FAILED] drag the divider, then drag it again
    → nothing on the page changed at all
```

### Sliders, checkboxes, dropdowns, colours and files

assay moves every slider to the far end, ticks every checkbox and radio
button, picks a different option in every dropdown, sets every colour picker
to a different colour, and gives every file input a small file of the type
it accepts.

For these checks, assay only reports an error the page threw, for the same
reason as buttons. It can't know what a slider or a checkbox is supposed to
change. They still count as using the page, which the
[nothing responds](#a-page-where-nothing-responds) check needs.

### Tabs and expandable sections

During every check, assay reads each tab and section header on screen. A
control marked `aria-selected="true"` or `aria-expanded="true"` is telling
screen readers that the panel named in its `aria-controls` is showing. If
that panel isn't rendered at all, the page contradicts itself, and assay
reports:

```
F001 [FAILED] the panel a selected tab or open section controls is shown
    → "Tab 2" is marked selected and controls the panel "panel-1", but that panel is not shown, first seen at C004
```

A panel that is empty still counts as shown, since it has a box on the page.
Only a panel the browser doesn't render at all is reported.

### Labels and radio buttons in the markup

During every check, assay also reads how labels and radio buttons are wired
together, and reports three mistakes that can't be seen by looking at the
page:

- Two radio buttons in one group with the same value, so the form can't tell
  which was picked:

  ```
  F002 [FAILED] labels and radio buttons are linked correctly
      → two radio buttons in the "option" group both have the value "2", so the form cannot tell which of them was picked, first seen at C001
  ```

- A label whose `for` names an id that doesn't exist:

  ```
      → the label "Email" is linked to "emial", but nothing on the page has that id, first seen at C001
  ```

- Two labels linked to the same control, which leaves the control the second
  one was meant for without a label:

  ```
      → two labels are both linked to "star4", so one of them was meant for another control, which is left without a label, first seen at C001
  ```

### Fields whose placeholder fails their own pattern

assay reads every field with both a `pattern` and a placeholder. If the
field's own example fails its own pattern, nothing typed can pass, and a
form that requires the field can't be completed:

```
F001 [FAILED] the zip box accepts its own placeholder example
    → the placeholder shows "12345" as an example, but the pattern on this field, \d{5}, rejects it, so nothing typed can pass and a form that requires it cannot be completed
```

This is read from the markup rather than found by typing, because the field
that prompted it sits on a later step of a wizard that the checks never
reach. A placeholder with a space in it is left alone, since that's an
instruction (*Enter five digits*) rather than an example value.

### NaN, undefined and [object Object] on the page

During every check, assay looks for `NaN`, `undefined` and `[object Object]`
in the visible text and in every field. No page shows these on purpose. They
mean a value was used before it was set, or calculated from something that
isn't a number. assay reports:

```
F001 [FAILED] no NaN, undefined or [object Object] on the page
    → the page shows `NaN` where a value should be, "Total: NaN". This usually means a value was used before it was set, or calculated from something that is not a number, first seen at C008
```

It isn't reported from a check in which assay itself typed something that
isn't a number. A temperature converter given `Sample item` correctly shows
`NaN`, since that's the right answer to the question it was asked. An empty
field counts as a number here.

### A page where nothing responds

Because single checks don't require a button to do anything, a page whose
buttons are all wired to nothing would pass every one of them. So at the end
of the run, assay asks the question about the whole page. If controls were
used and nothing on the page ever changed, it reports:

```
C000 [FAILED] something on the page responds when used
    → nothing on the page changed after any control was used, 14 checks used what the page offers and none of them changed it, so the controls do not seem to be connected to any code
```

This caught a kanban board whose three Add buttons were wired to nothing.
Because it calls the whole page broken, it's only reported when:

- at least two different controls were used,
- not one check saw anything change anywhere on the page,
- assay reached every control on the page. A sortable table whose clickable
  cells were used but whose sorting headers weren't reached was once
  reported this way, and it sorted perfectly.
- the page still does nothing when opened again and given several seconds
  instead of a fraction of one, three times over. A page whose Retry starts a
  two-second load looks inert in the time a single check allows it.

---

## What assay can't check

assay doesn't know what a control is meant to do, so a page that runs but
does the wrong thing, like a total that adds wrongly, usually passes. To
check what a control should do, write acceptance criteria and pass them from
Python: `check(folder, criteria=[...])` takes cases with their own actions
and expected results, and those expectations are checked as written.
