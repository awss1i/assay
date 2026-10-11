1. **What changed:** In the "Add Expense" click handler, the guard on the parsed amount became `amt <= 0` instead of the original `amt < 0`.
   **What goes wrong:** An expense with an amount of 0 is silently rejected: clicking Add Expense does nothing and no row is added.
   **How to see it:** On a freshly loaded page type "Free gift" in the description box, type `0` in the amount box, and click Add Expense; no row appears in the table.
2. **What changed:** In the "Add Expense" click handler, the amount cell is now set with `tdAmt.textContent = total.toFixed(2)` instead of the original `tdAmt.textContent = amt.toFixed(2)`.
   **What goes wrong:** The Amount column of each new row shows the running total from before that expense was added (the first row always shows 0.00) rather than the amount that was entered.
   **How to see it:** On a freshly loaded page type "Lunch" in the description box, type `15` in the amount box, and click Add Expense; the new row's Amount cell shows 0.00 while the summary's Total shows 15.00.
3. **What changed:** In the Delete button's click handler, the call to `updateTotals()` was removed, so `total` is still decremented but the summary is never redrawn.
   **What goes wrong:** Deleting an expense removes its row, but the Total and Remaining Budget numbers keep their pre-deletion values until some other action triggers a refresh.
   **How to see it:** On a freshly loaded page, add "Lunch" with `15` and then "Coffee" with `20` (Total shows 35.00), then click the red Delete button in the "Lunch" row; the row disappears but Total still shows 35.00.
4. **What changed:** At the end of the script, the `input` listener for `updateTotals` was attached to `amtInput` (the Amount box) instead of the original `budgetInput` (the Budget box).
   **What goes wrong:** Typing a new value into the Budget box no longer updates the Remaining Budget figure, which only refreshes when an expense is added, deleted, or when the Amount box is typed in.
   **How to see it:** On a freshly loaded page type `100` in the Budget box (Remaining stays 0.00), add "Lunch" with `15` (Remaining becomes -85.00), then change the Budget box from `100` to `200`; the Remaining Budget figure does not move.
5. **What changed:** In `updateTotals()`, `const remaining = budget - total;` became `const remaining = total - budget;`.
   **What goes wrong:** Remaining Budget always shows the negative of the correct value, so spending under the budget appears as a negative number.
   **How to see it:** On a freshly loaded page type `100` in the Budget box, type "Lunch" in the description box and `15` in the amount box, and click Add Expense; the summary displays "Remaining Budget: $-85.00" instead of $85.00.