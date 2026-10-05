# opencode / gpt-oss-120b

75 programs, from the objectives in `../../../objectives.txt`.

`truth` is what a person found by opening and using each program. `assay` is what the tool reported, and for a broken program, whether it flagged the actual bug, as judged by hand in [`verdicts.txt`](verdicts.txt).

| # | objective | truth | assay | seconds | notes |
|---|---|---|---|---|---|
| 01 | counter | works | clean | 9 | Increment adds one, Reset zeroes it and both stay live afterwards |
| 02 | converter | works | clean | 5 | both boxes convert each other as you type, exact at 0, 100 and -40 and back from 212F |
| 03 | stopwatch | works | clean | 8 | Start runs, Stop freezes, Start resumes rather than restarting (1.65 to 3.05), Lap records and Reset clears display and laps |
| 04 | todo | works | clean | 31 | Add appends the typed task and each Delete removes its own row |
| 05 | notes | works | clean | 4 | Add Note makes an editable note and its delete removes that note |
| 06 | cart | works | clean | 17 | each Add puts its item in the basket, repeats raise the quantity, and the subtotals and total follow to $2.57 |
| 07 | kanban | works | clean | 9 | Add Card appends to its column and the arrow moves a card to the next one |
| 08 | sortviz | works | clean | 17 | Shuffle randomises fifty bars and Sort animates through to zero inversions |
| 09 | wizard | works | clean | 11 | Next walks Account, Personal and Confirm, the review shows what was entered and Back returns |
| 10 | accordion | works | clean | 11 | each header opens its own panel and closes whichever was open |
| 11 | paintgrid | works | clean | 21 | cells take colour on click and Clear empties the grid |
| 12 | tictactoe | works | clean | 11 | clicks alternate X and O with the turn indicator following |
| 13 | memory | works | clean | 39 | cards flip face up on click and a non-matching pair turns back |
| 14 | minesweeper | works | clean | 11 | a click reveals its number and flood-fills the empty neighbours |
| 15 | draw | works | clean | 26 | strokes draw wherever they are made, Clear empties the canvas and it draws again afterwards |
| 16 | chart | works | clean | 30 | a comma-separated list is drawn as bars and a single value redraws as one |
| 17 | signature | works | clean | 32 | strokes draw, Undo removes exactly one, Clear empties the pad and it signs again |
| 18 | snake | works | clean | 22 | it runs from load and the arrow keys steer it |
| 19 | tetris | works | clean | 19 | pieces fall on their own and left, right and rotate all act |
| 20 | breakout | works | clean | 22 | the ball moves on its own and both arrows steer the paddle |
| 21 | bounce | works | clean | 44 | Add Ball and Remove Ball change the count and Pause freezes them all and relabels itself Resume |
| 22 | signup | works | clean | 15 | a bad email and a password under six characters each raise their own message, and a valid pair shows the success line |
| 23 | quiz | works | clean | 17 | Submit marks the five checked answers and reports the score |
| 24 | password | works | clean | 12 | Generate gives a different password every press and the length control sets it exactly, 20 meaning 20 |
| 25 | search | works | clean | 5 | typing narrows the list to matches, nonsense leaves none, and clearing restores all twenty |
| 26 | todo2 | works | clean | 23 | Enter adds, the checkbox drops the count, All/Active/Done filter correctly and Clear completed removes the ticked ones |
| 27 | notes2 | works | clean | 66 | Add Note stores title and body, Search filters live, and the notes survive a reload |
| 28 | cart2 | works | clean | 53 | changing a quantity retotals the line and the cart, and the promo code takes ten percent off (126.95 to 114.26) |
| 29 | kanban2 | works | clean | 20 | the plus button adds a card to its column and the board survives a reload |
| 30 | paint2 | broken | found | 56 | Undo is one press behind. Two strokes give 6 then 12 ink, the first Undo leaves 12 and the second gives back 6, and drawing itself is correct |
| 31 | tictactoe2 | works | clean | 14 | the computer answers every move and won, and Play Again clears the board while keeping the score |
| 32 | memory2 | works | clean | 11 | cards flip, the move counter advances and a non-matching pair turns back over |
| 33 | minesweeper2 | works | clean | 11 | a click reveals its number and flood-fills the empties, right click plants a flag and the mine counter follows |
| 34 | snake2 | works | clean | 25 | it runs from load, the arrows steer it, walls end the game, eating raises the score and the high score survives a reload |
| 35 | tetris2 | works | clean | 46 | pieces fall on their own, all three keys act and Pause freezes the board |
| 36 | breakout2 | broken | **missed** | 19 | update() moves the paddle and never the ball. The ball is drawn every frame at its starting spot, the paddle follows the pointer, and whatever is pressed the game cannot be played (bench/checks/breakout2.py) |
| 37 | draw2 | broken | found | 48 | it throws "Cannot access 'historyStack' before initialization" on load, so the script never runs and the canvas takes no stroke at all |
| 38 | chart2 | works | clean | 42 | Add Sample Data draws the bars, the button switches to a line and back, and Clear Data empties it |
| 39 | signup2 | works | clean | 12 | Sign Up stays disabled and names the reason for a bad email, a weak password or a mismatch, and enables only when all three are right |
| 40 | quiz2 | works | clean | 5 | Next walks the questions and the end shows a review of each answer against the correct one |
| 41 | search2 | works | clean | 15 | typing narrows the table to matching rows and clearing restores all twenty-one |
| 42 | wizard2 | broken | **missed** | 11 | every step advances with valid values, but the final Submit tests `!!data.zip` where it means `!data.zip`, so a filled ZIP always answers "Please complete all fields before submitting." and the form can never be sent (bench/checks/wizard2.py) |
| 43 | clock2 | works | clean | 4 | every clock ticks and the toggle switches all zones between 24 hour and am/pm |
| 44 | calc2 | works | clean | 55 | 7+8=15, 9x3=27, 50/4=12.5, 10-25=-15 and the sign flip is right too |
| 45 | timer2 | works | clean | 7 | it counts down from what is entered, Pause freezes it, Resume carries on and Reset clears it |
| 46 | gallery2 | works | clean | 27 | clicking a thumbnail opens the lightbox overlay |
| 47 | dashboard2 | works | clean | 5 | the bars render and a narrower date range redraws fewer of them with the visible total following (16131 to 11047) |
| 48 | markdown2 | works | clean | 5 | headings, bold and links render as you type and the word count follows |
| 49 | routes2 | works | clean | 19 | each link sets the hash and switches the view, and a deep link still shows its view after a reload |
| 50 | async2 | works | clean | 24 | the list arrives after its delay and the filter narrows it live |
| 51 | spreadsheet | broken | found | 47 | the grid never builds. The script that wires the cells runs before the block defining onFocus, so it throws on the first cell and the table is left with no rows at all |
| 52 | treeview | works | clean | 27 | four levels deep, folders expand and collapse, collapsing the root leaves exactly one row, and the counter tracks the visible rows exactly |
| 53 | sortable | works | clean | 11 | all three headers sort and reverse on a second press, and Age and Joined really do compare with Number() and Date() rather than as text |
| 54 | pagination | works | clean | 4 | ten to a page across five pages, items 41-47 on the last, the indicator tracks it, and Previous and Next each disable themselves at their end |
| 55 | tabs | works | clean | 20 | each tab shows only its own panel, and with a tab focused the arrow keys step between them while Home and End jump to the first and last |
| 56 | modal | works | clean | 8 | the button opens it over a 50% black dim, a click inside is ignored, a click outside and Escape both close it, and focus goes back to the opening button |
| 57 | autocomplete | works | clean | 5 | typing narrows the country list, the down arrow walks it, Enter puts the highlighted country in the box and closes the list, and Escape closes it leaving what was typed |
| 58 | reorder | broken | found | 7 | nothing can ever be reordered. dragenter inserts a placeholder li under the cursor, and the placeholder is not one of the items the handlers were attached to, so nothing calls preventDefault on its dragover, and no drop event fires at all, only dragend, and the order line stays 1 2 3 4 5 6 |
| 59 | multiselect | works | clean | 11 | a plain click replaces the selection, ctrl-click adds and removes again, shift-click takes the range from the anchor, and the Selected count is right at every step |
| 60 | splitpane | works | clean | 5 | the bar drags both ways as often as you like, the percentages track it, and neither pane goes below 10% however far past the edge you pull |
| 61 | invoice | works | clean | 7 | starts empty, Add Line Item appends a row, and 3 x 333p, 7 x 99p and 9 x 450p give 999p, 693p and 4050p with a £57.42 subtotal, £11.48 tax and £68.90 total |
| 62 | calendar | works | clean | 9 | prev and next walk the months, February 2024 gives 29 days and 2023 gives 28, every month starts in the right column of a Sunday-first grid, and today is marked |
| 63 | stepper | works | clean | 21 | plus and minus clamp at 10 and 1 and disable themselves there, and the typed route clamps too, 99 becomes 10, 0 and -3 become 1, and the total follows at 9.99 a unit |
| 64 | filtersort | works | clean | 15 | the box narrows the rows to the ones that match and a nonsense term empties the table, sorting survives filtering, and filtering after sorting keeps the order and loses no rows |
| 65 | undoredo | works | clean | 5 | undo steps back a character at a time and lights Redo, Redo puts it back, and typing after an undo greys Redo out rather than leaving the old branch reachable |
| 66 | zoompan | works | clean | 33 | the readout is right at every scale. After zooming in twice, a 120px drag moves the world point by exactly 83.33 and it stays under the pointer, and x1.2 against x1/1.2 returns exactly to 1 |
| 67 | palette | works | clean | 29 | clicking a shape selects it and a swatch then recolours that shape and neither of the other two, and a swatch pressed with nothing selected leaves the canvas pixel for pixel identical |
| 68 | infinite | works | clean | 47 | twenty rows to start, twenty more on each scroll to the bottom of its scrolling container up to sixty, then it says there is no more to load and stops appending |
| 69 | formarray | works | clean | 9 | the summary is refreshed by its own Update Summary button rather than live, and it is right every time, completed people listed, a name with no age left out, and a removed pair gone |
| 70 | diff | works | clean | 11 | side by side, alpha and gamma come back unchanged, beta and delta removed, GAMMA and epsilon added, and editing either pane redoes the comparison |
| 71 | pomodoro | works | clean | 8 | the phases really do alternate 25:00 and 05:00 round after round, Pause freezes the clock where it stood, Start resumes from there, Skip jumps to the other phase, and the round count rises once per full cycle |
| 72 | survey | works | clean | 9 | yes and no lead to different questions and Back walks a real history stack, though every path is only two questions deep and the result screen has no Back of its own, and the end lists the path taken |
| 73 | seatmap | works | clean | 11 | the booked seats refuse every click and cost nothing, a free seat toggles on and off, and the total counts only the seats currently chosen |
| 74 | cube3d | broken | found | 26 | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour |
| 75 | matrix | broken | **missed** | 9 | it multiplies the grids element by element instead of multiplying the matrices. cCells[i].value = aVal * bVal, so 1..9 times 9..1 gives 9 16 21 / 24 25 24 / 21 16 9 and the working shown reads 1 x 9 = 9 rather than a sum of three products |

**Programs that work:** 67 of 75, checked by hand.

**What assay found:**

- the actual bug in 5 of the 8 broken programs, missing 36_breakout2, 42_wizard2, 75_matrix
- 0 false alarms across the 67 working programs
- 0 flags on broken programs that are not their bug
