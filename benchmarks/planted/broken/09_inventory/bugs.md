1.
- **What changed:** In `renderTable`, the plus button's click handler now calls `changeQty(index, 2)`; it was `changeQty(index, 1)`.
- **What goes wrong:** Clicking the "+" button increases an item's quantity by two instead of one.
- **How to see it:** On a freshly loaded page the total reads 1; click the "+" button in the Apples row once and the total jumps to 3 (up by 2) instead of 2.

2.
- **What changed:** In `updateTotal`, the sum is now computed as `items.reduce((sum, it) => sum + it.qty, 1)`; the `reduce` previously started from `0`.
- **What goes wrong:** The "Total units" counter always reads exactly one more than the real sum of all quantities.
- **How to see it:** On a freshly loaded page, all three items have quantity 0, yet "Total units" already shows 1.

3.
- **What changed:** In `renderTable`, the low-stock note condition is now `if (item.qty >= 3)`; it was `if (item.qty < 3)`.
- **What goes wrong:** When the page loads, no "Low stock" label appears even though every item's quantity is below the low-stock threshold.
- **How to see it:** Load the page and look at the Note column: all three rows are empty although Apples, Bananas and Oranges all show quantity 0; a single "+" click on any row (quantity becomes 2) makes its label appear, confirming only the initial render failed to show it.

4.
- **What changed:** In `changeQty`, the line `document.getElementById('qty-' + idx).textContent = newQty;` (which redrew the quantity cell after each change) was removed.
- **What goes wrong:** The Quantity column never changes after any "+" or "−" click, even though the note and the total do update.
- **How to see it:** On a freshly loaded page, click the "+" button in the Bananas row three times; the Bananas row still shows 0 in the Quantity column while "Total units" climbs to 7.

5.
- **What changed:** In `changeQty`, the line `if (newQty < 0) return;` that prevented quantities from dropping below zero was removed.
- **What goes wrong:** Pressing "−" on an item with no stock drives its quantity into negative values, dragging the total negative as well.
- **How to see it:** On a freshly loaded page, click the "−" button in the Oranges row six times; "Total units" falls to -5, while on a working page it would stop at 0.