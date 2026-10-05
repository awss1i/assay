# The generated benchmark

*Written by `score.py`. Every number here comes from running it. Which flag is a broken program's actual bug is judged by hand in each folder's `verdicts.txt`.*

225 programs, written to the 75 objectives in [`objectives.txt`](objectives.txt) by dsh, no-harness, opencode on gpt-oss-120b. A person opened and tested every one by hand, and assay is scored against that answer key.

**20 of the 225 are broken.** The rest work.

## Contents

- [What It Found](#what-it-found)
- [The Broken Programs](#the-broken-programs)
- [Where the Programs Came From](#where-the-programs-came-from)

## What It Found

- **The actual bug in 15 of the 20 broken programs.** A flag on a broken program only counts if it is that program's bug.
- **0 false alarms** on the 205 working programs.
- **0 flags on broken programs that are not their bug.**

Of the 15 programs assay flagged, **15** were flagged for their actual bug.

Per program, the median is 14 seconds, 221 of 225 finish inside a minute, and the slowest took 3.9 minutes. Measured on AMD Ryzen 7 255 w/ Radeon 780M Graphics, Linux 7.2.6-200.fc44.x86_64, Python 3.14.7, Chromium 153.0.8010.12, Playwright 1.63.0.

Misses and false alarms are counted separately because a false alarm costs more: it sends someone to change code that was right.

There is no single accuracy percentage, because it would be misleading: 205 of these 225 programs work, so a tool that called everything clean without opening a browser would score 91%.

## The Broken Programs

Every program is in this repository, so you can open any of them and check.

| program | what is wrong | assay |
|---|---|---|
| [`dsh/30_paint2`](programs/dsh/gpt-oss-120b/30_paint2/index.html) | only the top-left 200 of an 802px canvas draws, because ctx.scale(4,4) runs against a 200px backing store while getMousePos divides by 4. Every other control including Undo is correct | found |
| [`dsh/34_snake2`](programs/dsh/gpt-oss-120b/34_snake2/index.html) | it dies after a few seconds and nothing restarts it, because clearInterval is called without nulling gameInterval, so the Space handler's !gameInterval is never true | found |
| [`dsh/37_draw2`](programs/dsh/gpt-oss-120b/37_draw2/index.html) | Undo is one press behind. Two strokes give 1224 then 2448 ink, the first Undo leaves 2448 and the second gives back 1224, and drawing, Redo and Clear are correct | found |
| [`dsh/52_treeview`](programs/dsh/gpt-oss-120b/52_treeview/index.html) | expanding, collapsing and hiding descendants are all correct, but the counter queries 'li, li > span' so every visible folder is counted twice, six rows on screen and it reads 10 | **missed** |
| [`dsh/60_splitpane`](programs/dsh/gpt-oss-120b/60_splitpane/index.html) | the first drag works and then the bar can never be grabbed again. Both panes are set to widths summing to 100% of the container, which squeezes the flex divider from 5px to 0px, so the minimum is unreachable and the split is frozen | found |
| [`dsh/74_cube3d`](programs/dsh/gpt-oss-120b/74_cube3d/index.html) | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour | found |
| [`no-harness/27_notes2`](programs/no-harness/gpt-oss-120b/27_notes2/index.html) | throws Missing initializer in const declaration, so the script never runs | found |
| [`no-harness/29_kanban2`](programs/no-harness/gpt-oss-120b/29_kanban2/index.html) | Add does nothing at all, on any column, so there is never a card to drag | found |
| [`no-harness/36_breakout2`](programs/no-harness/gpt-oss-120b/36_breakout2/index.html) | the click launches the ball downward, not up. The launch angle gives a positive dy although its comment says 45 degrees upward, so unless the paddle happens to sit under the ball the first click costs a life. Clicked under it, the ball bounces and the game plays (bench/checks/breakout2.py) | **missed** |
| [`no-harness/42_wizard2`](programs/no-harness/gpt-oss-120b/42_wizard2/index.html) | step two can never be completed. The ZIP field carries pattern="\\d{5}", an escaped backslash, so 12345 fails checkValidity and only a literal backslash followed by five d's passes | found |
| [`no-harness/55_tabs`](programs/no-harness/gpt-oss-120b/55_tabs/index.html) | selection and the arrow, Home and End keys all track correctly, but every panel goes blank after the first switch. .panel is display:none and only [hidden=false] shows it, while the script reveals a panel by removing the attribute | found |
| [`no-harness/74_cube3d`](programs/no-harness/gpt-oss-120b/74_cube3d/index.html) | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour | found |
| [`opencode/30_paint2`](programs/opencode/gpt-oss-120b/30_paint2/index.html) | Undo is one press behind. Two strokes give 6 then 12 ink, the first Undo leaves 12 and the second gives back 6, and drawing itself is correct | found |
| [`opencode/36_breakout2`](programs/opencode/gpt-oss-120b/36_breakout2/index.html) | update() moves the paddle and never the ball. The ball is drawn every frame at its starting spot, the paddle follows the pointer, and whatever is pressed the game cannot be played (bench/checks/breakout2.py) | **missed** |
| [`opencode/37_draw2`](programs/opencode/gpt-oss-120b/37_draw2/index.html) | it throws "Cannot access 'historyStack' before initialization" on load, so the script never runs and the canvas takes no stroke at all | found |
| [`opencode/42_wizard2`](programs/opencode/gpt-oss-120b/42_wizard2/index.html) | every step advances with valid values, but the final Submit tests `!!data.zip` where it means `!data.zip`, so a filled ZIP always answers "Please complete all fields before submitting." and the form can never be sent (bench/checks/wizard2.py) | **missed** |
| [`opencode/51_spreadsheet`](programs/opencode/gpt-oss-120b/51_spreadsheet/index.html) | the grid never builds. The script that wires the cells runs before the block defining onFocus, so it throws on the first cell and the table is left with no rows at all | found |
| [`opencode/58_reorder`](programs/opencode/gpt-oss-120b/58_reorder/index.html) | nothing can ever be reordered. dragenter inserts a placeholder li under the cursor, and the placeholder is not one of the items the handlers were attached to, so nothing calls preventDefault on its dragover, and no drop event fires at all, only dragend, and the order line stays 1 2 3 4 5 6 | found |
| [`opencode/74_cube3d`](programs/opencode/gpt-oss-120b/74_cube3d/index.html) | the canvas never shows anything. The shaders compile, the loop runs and 24 line indices are drawn every frame, but the uploaded MVP leaves every one of the eight corners outside the near and far clip planes (w comes out +/-1 while z is about +/-5), so the whole cube is clipped away and the canvas stays its clear colour | found |
| [`opencode/75_matrix`](programs/opencode/gpt-oss-120b/75_matrix/index.html) | it multiplies the grids element by element instead of multiplying the matrices. cCells[i].value = aVal * bVal, so 1..9 times 9..1 gives 9 16 21 / 24 25 24 / 21 16 9 and the working shown reads 1 x 9 = 9 rather than a sum of three products | **missed** |

## Where the Programs Came From

Three sources, so the programs don't all come from one tool.

- [`dsh` on `gpt-oss-120b`](programs/dsh/gpt-oss-120b/results.md): 69 of 75 work
- [`no-harness` on `gpt-oss-120b`](programs/no-harness/gpt-oss-120b/results.md): 69 of 75 work
- [`opencode` on `gpt-oss-120b`](programs/opencode/gpt-oss-120b/results.md): 67 of 75 work

---

Reproduce this with `python bench/score.py`. It needs no API key or network: the programs are in the repository and assay runs them in a local browser.

