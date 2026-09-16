# dsh / gpt-oss-120b

75 programs, from the objectives in `../../../objectives.txt`.

`truth` is what a person established by opening the program and driving it. `assay` is what the tool said on its own. They are separate columns because the whole point is to compare them.

| # | objective | truth | assay | agree | why the truth is what it is |
|---|---|---|---|---|---|
| 01 | counter | works | clean | ok | Increment adds one per press, Reset zeroes it, and both stay live afterwards |
| 02 | converter | works | clean | ok | both boxes convert each other as you type, exact on nine values including -40, and clearing one empties the other |
| 03 | stopwatch | works | clean | ok | Start runs, Stop freezes, Start resumes rather than restarting, Lap appends accurate times to the list, Reset clears display and laps |
| 04 | todo | works | clean | ok | Add and Enter both append the typed task, the field clears, blank is refused, and each Delete removes its own row |
| 05 | notes | works | clean | ok | Add Note makes a textarea you can type into, and each note's x deletes that note and no other |
| 06 | cart | works | clean | ok | each Add puts its item in the basket, repeats raise the quantity, Remove lowers it, and the total is right at every step |
| 07 | kanban | works | clean | ok | Add Card prompts and appends to its column, the arrow moves a card right and then hides itself in Done, where Add is deliberately off |
| 08 | sortviz | works | clean | ok | Shuffle randomises fifty bar heights and Sort animates a bubble sort down to zero inversions in about a minute |
| 09 | wizard | works | clean | ok | Next walks all three steps, fields carry into the review, Submit lands and Back returns to the previous step |
| 10 | accordion | works | clean | ok | each of the five headers opens its own panel and closes whichever was open |
| 11 | paintgrid | works | clean | ok | cells take the current swatch colour, eight swatches all select, Clear empties the grid and painting works again after it |
| 12 | tictactoe | works | clean | ok | clicks alternate X and O, three in a row is announced, the board stops accepting moves after a win, and Reset starts a fresh game |
| 13 | memory | works | clean | ok | a card flips, a non-matching second card turns both back, and a real pair stays face up |
| 14 | minesweeper | works | clean | ok | left click reveals and flood-fills the empty neighbours, right click plants a flag |
| 15 | draw | works | clean | ok | strokes accumulate wherever they are drawn, Clear empties the canvas and drawing works again afterwards |
| 16 | chart | works | clean | ok | Add draws a bar per value, exactly proportional: 10, 50, 30 and 100 come out 72, 200, 136 and 360 px above a 40px baseline |
| 17 | signature | works | clean | ok | strokes draw, Undo removes exactly the last one (852 ink back to 426), Clear empties the pad and it draws again afterwards |
| 18 | snake | works | clean | ok | it runs on its own and all four arrows steer the head the right way, refusing only a straight reversal |
| 19 | tetris | works | clean | ok | pieces fall by themselves, left and right move, up rotates, down drops, full rows clear and score |
| 20 | breakout | works | clean | ok | the ball bounces off walls, bricks and paddle, both arrows slide the paddle, and a missed ball resets to centre |
| 21 | bounce | works | clean | ok | Add puts another ball on the canvas, Remove takes one off, and Pause freezes every ball and relabels itself Resume |
| 22 | signup | works | clean | ok | a bad email and a short password each raise their own message, and a valid pair shows the success line |
| 23 | quiz | works | clean | ok | Submit scores the five checked answers and reports the total |
| 24 | password | works | clean | ok | Generate gives a different password every press and the length slider sets it exactly, 20 meaning 20 |
| 25 | search | works | clean | ok | typing in the box filters the country list live, and clearing it brings every country back |
| 26 | todo2 | works | clean | ok | Enter adds, the checkbox ticks and drops the count, All/Active/Done each filter correctly, Clear completed removes the ticked ones and double-click edits in place |
| 27 | notes2 | works | clean | ok | Add Note stores title and body, Search filters live, Pin lifts a note to the top and relabels itself Unpin, Delete removes it and everything survives a reload |
| 28 | cart2 | works | clean | ok | changing a quantity updates that subtotal and the total, the promo code takes 10 percent off (12.81 to 11.53), and Remove drops the line and retotals |
| 29 | kanban2 | works | clean | ok | Add Card appends to To Do, a card drags into another column, and the board and counts survive a reload |
| 30 | paint2 | broken | flagged | ok | only the top-left 200 of an 802px canvas draws, because ctx.scale(4,4) runs against a 200px backing store while getMousePos divides by 4; every other control including Undo is correct |
| 31 | tictactoe2 | works | clean | ok | the minimax computer answers every move and won three straight, the board clears between rounds and Reset Scores zeroes the tally |
| 32 | memory2 | works | clean | ok | a card flips and the move counter and timer advance, and a non-matching pair turns back over |
| 33 | minesweeper2 | works | clean | ok | left click reveals and flood-fills the empty neighbours, right click flags and unflags with the mine count following |
| 34 | snake2 | broken | flagged | ok | it dies after a few seconds and nothing restarts it, because clearInterval is called without nulling gameInterval, so the Space handler's !gameInterval is never true |
| 35 | tetris2 | works | clean | ok | pieces fall on their own, all four keys act, and Pause freezes the board and relabels itself Resume |
| 36 | breakout2 | works | clean | ok | the ball moves on its own and both arrows steer the paddle |
| 37 | draw2 | broken | flagged | ok | Undo is one press behind: two strokes give 1224 then 2448 ink, the first Undo leaves 2448 and the second gives back 1224; drawing, Redo and Clear are correct |
| 38 | chart2 | works | clean | ok | the checkbox swaps five bar rects for a line polyline and back, over the same axes |
| 39 | signup2 | works | clean | ok | Submit stays disabled until the email is valid, the password scores five of five and confirm matches, and the strength bar tracks what is typed |
| 40 | quiz2 | works | clean | ok | Next and Previous walk the questions and Finish shows a review of each answer against the correct one |
| 41 | search2 | works | clean | ok | filtering narrows twenty rows to two for 'united' and none for nonsense, the count line follows, and clearing restores them |
| 42 | wizard2 | works | clean | ok | Next refuses a blank or malformed field, the review lists what was typed, and Previous goes back; Next is hidden on the last step |
| 43 | clock2 | works | clean | ok | every clock ticks and the toggle switches all zones between 12 and 24 hour |
| 44 | calc2 | works | clean | ok | 7+8=15, 9x3=27, 50/4=12.5, 10-25=-15, and the sign flip and percent keys are right too |
| 45 | timer2 | works | clean | ok | it counts down from what is entered, Pause freezes it, Resume carries on from there and Reset restores the set time |
| 46 | gallery2 | works | clean | ok | clicking a thumbnail opens the lightbox overlay |
| 47 | dashboard2 | works | clean | ok | a date range regenerates the bars, the line points and the pie together (8 days gives 8 of each, 16 gives 16), the total follows and a reversed range is refused |
| 48 | markdown2 | works | clean | ok | headings, bold and links render as you type and the word count follows |
| 49 | routes2 | works | clean | ok | the three links switch view and set the hash, and a deep link still shows its view after a reload |
| 50 | async2 | works | clean | ok | the list arrives after its delay and the filter narrows it live |
| 51 | spreadsheet | works | clean | ok | formulas compute, a dependent recomputes when a referenced cell changes, chains follow (A1 to C1 to D1), and a self-reference lands on NaN rather than hanging |
| 52 | treeview | broken | flagged | ok | expanding, collapsing and hiding descendants are all correct, but the counter queries 'li, li > span' so every visible folder is counted twice: six rows on screen and it reads 10 |
| 53 | sortable | works | clean | ok | all three headers sort and reverse on a second press, and Age and Joined really do compare with Number() and Date() rather than as text |
| 54 | pagination | works | clean | ok | ten to a page across five pages, items 41-47 on the last, the indicator tracks it, and Previous and Next each disable themselves at their end |
| 55 | tabs | works | clean | ok | each tab shows only its own panel, and with a tab focused the arrow keys step between them while Home and End jump to the first and last |
| 56 | modal | works | clean | ok | the button opens it over a 50% black dim, a click inside is ignored, a click outside and Escape both close it, and focus goes back to the opening button |
| 57 | autocomplete | works | clean | ok | typing narrows the country list, the down arrow walks it, Enter puts the highlighted country in the box and closes the list, and Escape closes it leaving what was typed |
| 58 | reorder | works | clean | ok | dragging a row lands it where you dropped it and the order line underneath agrees with the rows every time: 1 onto 4 gives 2 3 1 4 5 6, then 6 onto 1 gives 6 2 3 1 4 5 |
| 59 | multiselect | works | clean | ok | a plain click replaces the selection, ctrl-click adds and removes again, shift-click takes the range from the anchor, and the Selected count is right at every step |
| 60 | splitpane | broken | flagged | ok | the first drag works and then the bar can never be grabbed again: both panes are set to widths summing to 100% of the container, which squeezes the flex divider from 5px to 0px, so the minimum is unreachable and the split is frozen |
| 61 | invoice | works | clean | ok | unit prices in pence, and 3 x 333p and 7 x 99p give 999p and 693p with a £16.92 subtotal, £3.38 tax and £20.30 total, exact to the penny |
| 62 | calendar | works | clean | ok | prev and next walk the months, February 2024 gives 29 days and 2023 gives 28, every month starts in the right column of a Sunday-first grid, and today is marked |
| 63 | stepper | works | clean | ok | plus and minus clamp at 10 and 1 however long you hold them and the total follows at 10.00 a unit, but the box is readonly, so the typed route the objective asks about does not exist |
| 64 | filtersort | works | clean | ok | the box narrows the rows to the ones that match and a nonsense term empties the table, sorting survives filtering, and filtering after sorting keeps the order and loses no rows |
| 65 | undoredo | works | clean | ok | undo steps back a character at a time and lights Redo, Redo puts it back, and typing after an undo greys Redo out rather than leaving the old branch reachable |
| 66 | zoompan | works | clean | ok | the readout is right at every scale: after zooming in twice, a 120px drag moves the world point by exactly 83.33 and it stays under the pointer; zoom in is x1.2 and zoom out x0.8, so the pair does not return you to 1 |
| 67 | palette | works | clean | ok | clicking a shape selects it and a swatch then recolours that shape and neither of the other two, and a swatch pressed with nothing selected leaves the canvas pixel for pixel identical |
| 68 | infinite | works | clean | ok | twenty rows to start, twenty more on each scroll to the bottom up to sixty, then it says there is no more to load and stops appending |
| 69 | formarray | works | clean | ok | Add Person appends a name and age pair, the summary lists every completed one live, a name with no age is left out, and each Remove takes its own pair and drops it from the summary |
| 70 | diff | works | clean | ok | alpha and gamma come back unchanged, beta and delta removed, GAMMA and epsilon added, and editing either pane redoes the comparison |
| 71 | pomodoro | works | clean | ok | twenty-five minutes of work rolls into a five-minute break and back on its own, round after round, Pause freezes the clock where it stood, Start resumes from there and Skip jumps to the other phase; the round count rises when a work session ends |
| 72 | survey | works | clean | ok | yes and no lead to different questions, Back retraces the branch actually taken two levels deep and really rewinds it (answering the other way then goes somewhere else), and the end lists every question with the answer given |
| 73 | seatmap | works | clean | ok | the booked seats refuse every click and cost nothing, a free seat toggles on and off, and the total counts only the seats currently chosen |
| 74 | cube3d | broken | flagged | ok | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour |
| 75 | matrix | works | clean | ok | 1..9 times 9..1 gives 30 24 18 / 84 69 54 / 138 114 90, the working for cell (0,0) reads 1 x 9 + 2 x 6 + 3 x 3 = 30, and the number inputs refuse letters outright |

**What this pairing produced:** 69 of 75 programs work. Hand-established.

**What assay found here:**

- 6 of the 6 defects
- 0 false alarms across the 69 working programs
