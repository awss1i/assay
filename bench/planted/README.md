# The planted-bug set

*Written by `planted/score.py`. The checks, flags and times come from running it. Which planted bug each flag shows is judged by hand in each `verdict.txt`.*

10 programs with bugs added on purpose (50 in all, as listed in each `bugs.md`), and 10 working originals.

## Contents

- [What It Found](#what-it-found)
- [Every Planted Bug](#every-planted-bug)
- [How the Set Was Built](#how-the-set-was-built)

## What It Found

- **12 of the 50 planted bugs found.**
- **0 of the 10 working originals flagged**.
- **0 flags on broken programs that are not a planted bug.**
- **Grouped findings:** assay drew 10 links between findings. 10 of them match the answer key, 0 are wrong, and 0 that the key expects are missing.

Per program, the median is 23 seconds, 19 of 20 finish inside a minute, and the slowest took 62 seconds. Measured on AMD Ryzen 7 255 w/ Radeon 780M Graphics, Linux 7.2.6-200.fc44.x86_64, Python 3.14.7, Chromium 153.0.8010.12, Playwright 1.63.0.

## Every Planted Bug

### 01_bookmarks

24 checks, 4 flagged, 4 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | found | C016 `wrong-row@press Remove, with two saved`: Remove takes the row beneath the one pressed |
| 2 | found | F002 `never-shown@values typed into a list show up in the new row`: the row made does not carry the typed URL |
| 3 | found | C022 `forgot-on-reload@save two, reload, and they are still there`: saved under one key and read back under another, so a reload loses the list |
| 4 | found | F001 `count-off@the count of items matches the list`: a number counting the list reads -1 when empty |
| 5 | missed | every check that presses Save fills in both fields, so a blank title, or a title with no URL, is never sent |

### 02_poll

5 checks, 2 flagged, 2 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | no expectation of which screen a page opens on |
| 2 | found | F001 `computed@no NaN, undefined or [object Object] on the page: NaN`: NaN% in the visible text |
| 3 | missed | Spring's bar is left blank beside three that read NaN%, and nothing expects every bar to carry a figure |
| 4 | found | F002 `wiring@labels and radio buttons are linked correctly: two radio buttons in the "option" group both have the value "2", so the form cannot tell which of them was picked`: two choices carrying value 2 |
| 5 | missed | no vote is ever cast, so no radio is ever left checked |

### 03_recipe

3 checks, 0 flagged, 0 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | only 25 and nothing are typed into Servings, never 1, so the wrong rejection of 1 is never met |
| 2 | missed | Servings is a number box, so Chromium turns the NaN written back into an empty field, and the field staying empty instead of going back to 4 is a value judgement |
| 3 | missed | typing 25 fills in a quantity, so the page changed, and showing 25.00 instead of 25 is a value judgement |
| 4 | missed | typing 25 fills in one quantity cell, so the page changed, and that the other four stay empty is a value judgement |
| 5 | missed | no expectation that a table arrives filled |

### 04_flashcards

19 checks, 1 flagged, 1 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | front and back both carry text, and that they match is a value judgement |
| 2 | missed | no expectation of how many cards there are |
| 3 | found | F001 `opposites@Previous works as well as Next`: Previous never answers while Next always does |
| 4 | missed | pressing Shuffle asserts nothing, and it changes nothing to notice |
| 5 | missed | the card is clicked twice. The first click flips it and the second does nothing, which is also how a control that only switches on behaves, so it isn't flagged |

### 05_budget

19 checks, 2 flagged, 2 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | only 25 or nothing is typed as an amount, never 0 |
| 2 | found | F001 `never-shown@values typed into a list show up in the new row`: the row shows the running total from before it, 0.00, where 25 was typed |
| 3 | found | F002 `one-way@a total that follows the list also goes down`: the total follows the list up and not down |
| 4 | missed | typing into Budget leaves Remaining unchanged, but Budget has no button after it, and a field on its own is only required not to throw |
| 5 | missed | remaining does change, and the sign is a value judgement |

### 06_tagfilter

18 checks, 8 flagged, 1 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | the other eleven items hide, so the page changed |
| 2 | missed | items hiding is a change whichever ones hide |
| 3 | missed | a note saying nothing matches is not read against the list, and the one pair tried never shows it |
| 4 | found | C003 `went-back@click blue twice`: the tag goes back and the list stays filtered. C005 `went-back@click green twice`: the same, on another tag. C007 `went-back@click large twice`: the same, on another tag. C009 `went-back@click medium twice`: the same, on another tag. C011 `went-back@click red twice`: the same, on another tag. C013 `went-back@click round twice`: the same, on another tag. C015 `went-back@click small twice`: the same, on another tag. C017 `went-back@click square twice`: the same, on another tag |
| 5 | missed | the tag text is present, and that it is the wrong text is a value |

### 07_scheduler

20 checks, 4 flagged, 1 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | no expectation of what the days are called |
| 2 | missed | no expectation of how many slots a row has |
| 3 | missed | the summary names the wrong slot, which is a value judgement, and the one pair of neighbouring cells clicked is two header cells, so two cells in one row are never clicked together |
| 4 | found | C011 `one-behind-cell@click #grid > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(6) twice`: the square clicked is one press behind. C013 `one-behind-cell@click #grid > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(6) twice`: the same, on another square. C017 `one-behind-cell@click #grid > tbody:nth-child(2) > tr:nth-child(5) > td:nth-child(5) twice`: the same, on another square. C019 `one-behind-cell@click #grid > tbody:nth-child(2) > tr:nth-child(5) > td:nth-child(6) twice`: the same, on another square |
| 5 | missed | Slot 0 against Slot 1 is a value judgement |

### 08_colormix

6 checks, 0 flagged, 0 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | the swatch recolours when a slider moves, and that it is the wrong colour is a value judgement |
| 2 | missed | moving Blue recolours the swatch, so it answered, and the number beside it is a value |
| 3 | missed | moving Red changes nothing else, but a slider only has to survive being moved |
| 4 | missed | the swatch recolours, so the page changed, and a Hex field stuck at #000000 is a value |
| 5 | missed | the copy is not observable from the page |

### 09_inventory

19 checks, 0 flagged, 0 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | the total changes, so the page changed |
| 2 | missed | an off-by-one in a total is a value judgement |
| 3 | missed | nothing says a note should be there when the page loads |
| 4 | missed | the total and the low-stock note change, so the page changed, and that the Quantity column stays the same is a value judgement |
| 5 | missed | the total changes, and that it went negative is a value |

### 10_ratings

11 checks, 1 flagged, 1 of 5 planted bugs found.

| bug | assay | which finding |
|---|---|---|
| 1 | missed | the stars are clicked and Submit is pressed, but never in the same check. The comment box and Submit sit in different containers, so assay doesn't treat them as one form |
| 2 | missed | no check picks a star and then presses Submit, so no rating is ever recorded and there is no average to read |
| 3 | missed | no check picks a star and then presses Submit, so no rating is ever recorded and no entry is drawn |
| 4 | missed | no check picks a star and then presses Submit, so no rating is ever recorded and the box is never refilled |
| 5 | found | F001 `wiring@labels and radio buttons are linked correctly: two labels are both linked to "star4", so one of them was meant for another control, which is left without a label`: two labels pointing at star4 |

## How the Set Was Built

One harness and model wrote the programs from [`objectives.txt`](objectives.txt). A **different** harness and model put the bugs in, from the instruction in [`inject-prompt.txt`](inject-prompt.txt), which names no checker, no rule and no tool. Neither step was told assay exists. `generate.sh` and `inject.sh` are the two steps. assay's rules were developed with this set in view, so its score is in-sample.

Each broken program has a `bugs.md` from the model that added the bugs, and a `verdict.txt` recording, for each bug, whether assay caught it and with which finding. Findings are named by the rule and the check, not by case number, so verdicts stay correct when checks are added or reordered.

Deciding whether a failure is a particular planted bug is a judgement, so it's made by hand and written down, not matched by a script.

