# no-harness / gpt-oss-120b

75 programs, from the objectives in `../../../objectives.txt`.

`truth` is what a person established by opening the program and driving it. `assay` is what the tool said on its own. They are separate columns because the whole point is to compare them.

| # | objective | truth | assay | agree | why the truth is what it is |
|---|---|---|---|---|---|
| 01 | counter | works | clean | ok | Increment adds one, Reset zeroes it, and the count survives a reload |
| 02 | converter | works | clean | ok | both boxes convert each other as you type, exact at 0, 100, -40 and back from 212F |
| 03 | stopwatch | works | clean | ok | Start runs, Stop freezes, Start resumes rather than restarting (1.70 to 3.10), Lap records and Reset clears display and laps |
| 04 | todo | works | clean | ok | Add appends the typed task and each Delete removes its own row, leaving the others |
| 05 | notes | works | clean | ok | Add Note makes an editable note you can type into, and its x deletes that note |
| 06 | cart | works | clean | ok | each Add puts its item in the basket, repeats raise the quantity, and the subtotals and total follow (0.99, 1.98, then 4.47 with bread) |
| 07 | kanban | works | clean | ok | Add Card appends to its column and the arrow moves a card to the next one |
| 08 | sortviz | works | clean | ok | Shuffle randomises sixty bars and Sort animates a bubble sort through to zero inversions |
| 09 | wizard | works | clean | ok | Next walks the three steps, the button becomes Submit on the last, and Back returns |
| 10 | accordion | works | clean | ok | each header opens its own panel, closes whichever was open, and clicking the open one closes it |
| 11 | paintgrid | works | clean | ok | cells take colour on click, Clear empties the grid and painting works again afterwards |
| 12 | tictactoe | works | clean | ok | clicks alternate X and O with the turn indicator following, and Reset Game clears the board |
| 13 | memory | works | clean | ok | a card flips face up and a second one flips too, with non-matching pairs turning back |
| 14 | minesweeper | works | clean | ok | a safe click reveals its number, a mine ends the game, right click plants a flag and Restart deals a new board |
| 15 | draw | works | clean | ok | strokes draw wherever they are made, Clear empties the canvas and it draws again afterwards |
| 16 | chart | works | clean | ok | a comma-separated list is drawn as bars and a single value redraws as one |
| 17 | signature | works | clean | ok | strokes draw, Undo removes the last one, Clear empties the pad and it signs again afterwards |
| 18 | snake | works | clean | ok | it runs from load, dies at the wall if nobody steers, the arrows turn it, and Enter restarts it and it moves again |
| 19 | tetris | works | clean | ok | pieces fall on their own and left, right and rotate all act |
| 20 | breakout | works | clean | ok | the ball moves on its own and both arrows steer the paddle |
| 21 | bounce | works | clean | ok | Add Ball puts another on the canvas, Remove takes one off, and Pause freezes them all and relabels itself Resume |
| 22 | signup | works | clean | ok | a bad email and a password under eight characters or without a digit each raise their own message, and a valid pair shows the success line |
| 23 | quiz | works | clean | ok | Show My Score marks the five checked answers and reports the total |
| 24 | password | works | clean | ok | Generate gives a different password every press and the length control sets it exactly, 20 meaning 20 |
| 25 | search | works | clean | ok | typing narrows the country list to matches, nonsense gives none, and clearing restores all twenty-one |
| 26 | todo2 | works | clean | ok | Enter adds, the checkbox drops the count, All/Active/Done filter correctly and Clear completed removes the ticked ones |
| 27 | notes2 | broken | flagged | ok | throws Missing initializer in const declaration; the script never runs |
| 28 | cart2 | works | clean | ok | changing a quantity retotals the line and the cart, and the promo code takes ten percent off (214.70 to 193.23) |
| 29 | kanban2 | broken | flagged | ok | Add does nothing at all, on any column, so there is never a card to drag |
| 30 | paint2 | works | clean | ok | every stroke paints wherever it is made and Undo removes exactly one stroke at a time |
| 31 | tictactoe2 | works | clean | ok | the computer answers every move and won, the board stops accepting clicks after the win, and New Game clears it while keeping the score |
| 32 | memory2 | works | clean | ok | cards flip and the move counter and timer advance as you play |
| 33 | minesweeper2 | works | clean | ok | clicks reveal numbers and flood-fill the empty neighbours, with the mine counter shown |
| 34 | snake2 | works | clean | ok | it runs from load, dies at the wall if nobody steers, and Space restarts it with the score and high score updating |
| 35 | tetris2 | works | clean | ok | pieces fall on their own, left and right move them, and Pause freezes the board |
| 36 | breakout2 | broken | clean | **XX** | the paddle tracks the mouse, but the ball never launches. The click handler that its own comment says launches it only runs `if (gameOver)`, so a fresh game sits still whatever you press |
| 37 | draw2 | works | clean | ok | strokes draw, Undo removes exactly one at a time, Redo puts it back and Clear empties the canvas |
| 38 | chart2 | works | clean | ok | the button switches between line and bar and back, redrawing the same data |
| 39 | signup2 | works | clean | ok | Sign Up stays disabled and names the reason for a bad email, a weak password or a mismatch, and enables only when all three are right |
| 40 | quiz2 | works | clean | ok | Next and Previous walk the questions and the end shows a review of the answers given |
| 41 | search2 | works | clean | ok | typing narrows the table to matching rows, nonsense leaves none, and clearing restores all twenty-one |
| 42 | wizard2 | broken | flagged | ok | step two can never be completed: the ZIP field carries pattern="\\d{5}", an escaped backslash, so 12345 fails checkValidity and only a literal backslash followed by five d's passes |
| 43 | clock2 | works | clean | ok | every clock ticks and the toggle switches all zones between 12 and 24 hour |
| 44 | calc2 | works | clean | ok | 7+8=15, 9x3=27 and 50/4=12.5, with C clearing between sums |
| 45 | timer2 | works | clean | ok | it counts down from what is entered, Pause freezes it, Resume carries on and Reset restores the set time |
| 46 | gallery2 | works | clean | ok | clicking a thumbnail opens the lightbox overlay with its close control |
| 47 | dashboard2 | works | clean | ok | the charts render and a changed date range redraws them and updates the visible total |
| 48 | markdown2 | works | clean | ok | headings, bold and links render as you type and the word count follows |
| 49 | routes2 | works | clean | ok | the three links switch view and set the hash, and the view survives a reload |
| 50 | async2 | works | clean | ok | the list arrives after its delay and the filter narrows it live |
| 51 | spreadsheet | works | clean | ok | formulas compute, dependents and chains recompute on every edit, and a self-reference is refused with #CIRC! rather than hanging |
| 52 | treeview | works | clean | ok | three levels deep, each folder expands and collapses, a collapsed folder takes every descendant with it, and the counter matches the visible rows at all 16 |
| 53 | sortable | works | clean | ok | all three headers sort and reverse on a second press, and Age and Joined really do compare with Number() and Date() rather than as text |
| 54 | pagination | works | clean | ok | ten to a page across five pages, items 41-47 on the last, the indicator tracks it, and Previous and Next each disable themselves at their end |
| 55 | tabs | broken | clean | **XX** | selection and the arrow, Home and End keys all track correctly, but every panel goes blank after the first switch: .panel is display:none and only [hidden=false] shows it, while the script reveals a panel by removing the attribute |
| 56 | modal | works | clean | ok | the button opens it over a 50% black dim, a click inside is ignored, a click outside and Escape both close it, and focus goes back to the opening button |
| 57 | autocomplete | works | clean | ok | typing narrows the country list, the down arrow walks it, Enter puts the highlighted country in the box and closes the list, and Escape closes it leaving what was typed |
| 58 | reorder | works | clean | ok | dragging a row lands it where you dropped it and the order line underneath agrees with the rows every time: 1 onto 4 gives 2 3 1 4 5 6, then 6 onto 1 gives 6 2 3 1 4 5 |
| 59 | multiselect | works | clean | ok | a plain click replaces the selection, ctrl-click adds and removes again, shift-click takes the range from the anchor, and the Selected count is right at every step |
| 60 | splitpane | works | clean | ok | the bar drags both ways as often as you like, the percentages track it, and neither pane goes below 10% however far past the edge you pull |
| 61 | invoice | works | clean | ok | prices are shown in pounds rather than pence, and the arithmetic is exact anyway: 3 x 2.99 and 7 x 14.99 give 8.97 and 104.93, subtotal 154.40, tax 30.88, total 185.28 |
| 62 | calendar | works | clean | ok | prev and next walk the months, February 2024 gives 29 days and 2023 gives 28, every month starts in the right column of a Sunday-first grid, and today is marked |
| 63 | stepper | works | clean | ok | plus and minus clamp at 10 and 1 and disable themselves there, and the typed route clamps too: 99 becomes 10, 0 and -3 become 1, and the total follows at 9.99 a unit |
| 64 | filtersort | works | clean | ok | the box narrows the rows to the ones that match and a nonsense term empties the table, sorting survives filtering, and filtering after sorting keeps the order and loses no rows |
| 65 | undoredo | works | clean | ok | undo steps back a character at a time and lights Redo, Redo puts it back, and typing after an undo greys Redo out rather than leaving the old branch reachable |
| 66 | zoompan | works | clean | ok | the readout is right at every scale: after zooming in twice, a 120px drag moves the world point by exactly 83.33 and it stays under the pointer, and x1.2 against x1/1.2 returns exactly to 1 |
| 67 | palette | works | clean | ok | clicking a shape selects it and a swatch then recolours that shape and neither of the other two, and a swatch pressed with nothing selected leaves the canvas pixel for pixel identical |
| 68 | infinite | works | clean | ok | twenty rows to start, twenty more on each scroll to the bottom up to sixty, then it says there is no more to load and stops appending |
| 69 | formarray | works | clean | ok | Add Person appends a name and age pair, the summary lists every completed one live, a name with no age is left out, and each Remove takes its own pair and drops it from the summary |
| 70 | diff | works | clean | ok | alpha and gamma come back unchanged, beta and delta removed, GAMMA and epsilon added, and editing either pane redoes the comparison |
| 71 | pomodoro | works | clean | ok | twenty-five minutes of work rolls into a five-minute break and back on its own, Pause freezes the clock where it stood, Start resumes from there and Skip jumps to the other phase; the round count rises when a full work and break cycle ends |
| 72 | survey | works | clean | ok | yes and no lead to different questions, Back retraces the branch actually taken two levels deep and really rewinds it (answering the other way then goes somewhere else), and the end lists every question with the answer given |
| 73 | seatmap | works | clean | ok | the booked seats refuse every click and cost nothing, a free seat toggles on and off, and the total counts only the seats currently chosen |
| 74 | cube3d | broken | flagged | ok | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour |
| 75 | matrix | works | clean | ok | 1..9 times 9..1 gives 30 24 18 / 84 69 54 / 138 114 90, the working reads c00 = 1x9 + 2x6 + 3x3 = 30, and a letter in any cell is refused with an alert leaving the last result standing |

**What this pairing produced:** 69 of 75 programs work. Hand-established.

**What assay found here:**

- 4 of the 6 defects, missing 36_breakout2, 55_tabs
- 0 false alarms across the 69 working programs
