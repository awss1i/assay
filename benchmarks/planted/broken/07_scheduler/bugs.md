1.
- **What changed:** The `days` array at the top of the script — before it was `["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]`.
- **What goes wrong:** The last row of the grid says "Sunday" instead of "Friday", so a real Friday booking cannot be made and the week scheduled is not the work week.
- **How to see it:** Load the page and read the row labels down the left of the grid; the fifth row is labelled "Sunday" while the heading promises a five-day (Mon–Fri) week.

2.
- **What changed:** The column-building loop `for (let s = 0; s < slotCount; s++)` in the grid builder — before the comparison was `s < slotCount`, it is now `s <= slotCount`.
- **What goes wrong:** Every day row is built with five slot cells under four slot headers, so a phantom extra column of clickable cells with no header appears on the right of the grid.
- **How to see it:** Load the page and count the cells in any day row: there are five green cells beneath the four "Slot 1–4" headers; clicking the extra headerless cell behaves like a normal slot.

3.
- **What changed:** The per-cell construction `td.dataset.slot = s` — before it copied the loop variable `s`, it now copies the day index `dIdx`.
- **What goes wrong:** Every cell in a row is given the same slot number (equal to the day's position), so a booking is always stored and reported for the wrong slot — Wednesday's clicks are reported as "Slot 2", Monday's as "Slot 0", and clicking two different cells in the same row toggles the single shared slot.
- **How to see it:** On a fresh page, click Wednesday's cell in the Slot 3 column: the summary lists "Wednesday: Slot 2", not Slot 3. Then click another cell in Wednesday's row and the single summary entry vanishes.

4.
- **What changed:** In `toggleSlot`, the highlight update `td.classList.toggle('booked', booked[d][s])` — before it passed the new state, it now passes `!booked[d][s]`.
- **What goes wrong:** The orange highlight is applied a click late: the first click books the cell but leaves it green, and the second click (which actually cancels the booking) turns it orange.
- **How to see it:** On a fresh page, click any cell once: the summary lists it but the cell stays green; click it a second time: the cell turns orange even though it has now dropped out of the summary.

5.
- **What changed:** In `updateSummary`, the slot label `slots.push(\`Slot ${sIdx + 1}\`)` — before it added one to the index, it now uses `Slot ${sIdx}`.
- **What goes wrong:** The summary numbers slots 0–3, so the first slot is reported as "Slot 0", a number that matches none of the "Slot 1–4" headers.
- **How to see it:** On a fresh page, click a day's first slot cell and read the summary list: it reports "Slot 0" instead of "Slot 1".