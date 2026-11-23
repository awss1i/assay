1.
- **What changed:** the validation check in `update()` was `if (isNaN(val) || val < 1)`; it is now `if (isNaN(val) || val <= 1)`.
- **What goes wrong:** entering 1 serving, a valid positive integer, triggers the "Servings must be a positive integer." alert and stops the quantities from being recalculated.
- **How to see it:** on a fresh load, replace the value in the Servings field with 1 and press Tab; the alert pops up and no quantities are computed for 1 serving.

2.
- **What changed:** the invalid-input branch of `update()` used to restore the field with `servingsInput.value = lastValid;`; it now sets `servingsInput.value = val;`, writing the rejected value back into the field.
- **What goes wrong:** after any rejected entry the field is never restored to the last good value, and after clearing the field the literal text "NaN" is left behind in the input box.
- **How to see it:** on a fresh load, select all the text in the Servings field, delete it, and press Tab; after dismissing the alert the field shows "NaN" instead of reverting to 4.

3.
- **What changed:** in the quantity calculation in `update()`, the trailing-zero trim used to be `.replace(/\.00$/, '')`; it is now `.replace(/\.0$/, '')`, a pattern that never matches a `toFixed(2)` result.
- **What goes wrong:** integer quantities are displayed with trailing zeros ("8.00") instead of being trimmed to "8".
- **How to see it:** on a fresh load, change Servings from 4 to 6 and press Tab; the quantity shown appears as "6.00" rather than "6".

4.
- **What changed:** the render loop in `update()` used to write into `row.querySelector('.qty')`, the row being iterated; it now writes into `rows[3].querySelector('.qty')`, always the fourth row (Eggs).
- **What goes wrong:** only the Eggs row's quantity cell ever changes, and it receives the value computed for the last iterated row (Milk) instead of its own; the other four rows stay empty or stale.
- **How to see it:** on a fresh load, change Servings from 4 to 8 and press Tab; the only cell that fills in is Eggs, and it shows 8.00 (Milk's number) instead of 16, while Flour, Sugar, Butter, and Milk remain empty.

5.
- **What changed:** the script used to call `update();` once during startup, right after the function definition and before the change listener was attached; that initial invocation was removed.
- **What goes wrong:** on a fresh page load the entire Quantity column is empty even though the input already reads 4, until the user edits the servings value.
- **How to see it:** load the page (or reload it) and look at the table before touching anything; all five quantity cells are blank despite Servings showing 4.