1. - **What changed:** `render()` — the line that was `backEl.textContent = card.a` is now `backEl.textContent = card.q`.
   - **What goes wrong:** Flipping a card shows the question text on the answer face instead of the answer.
   - **How to see it:** From a freshly loaded page, click the card once; the back face displays "What is the capital of France?" where "Paris" should be.
2. - **What changed:** the Next button's click handler — the guard was `if(index < order.length-1)` and is now `if(index < order.length-2)`.
   - **What goes wrong:** The last card of the deck can never be shown because Next stops advancing one card too early.
   - **How to see it:** From a freshly loaded page, click "Next" 5 times; the sequence stops at "First element of periodic table?" and no further clicks ever reach "Speed of light (m/s)?".
3. - **What changed:** the Previous button's click handler — the guard was `if(index>0)` and is now `if(index<0)`.
   - **What goes wrong:** The "Previous" button never goes back in the deck, no matter how many times it is clicked.
   - **How to see it:** From a freshly loaded page, click "Next" twice so the card shows "2 + 2 = ?", then click "Previous" three times; the card still shows "2 + 2 = ?".
4. - **What changed:** the Shuffle button's click handler — it previously ended with `index=0; render();` and now ends with `index=0;` (the redraw was dropped).
   - **What goes wrong:** Shuffling reorders the deck and resets the position, but the screen is never redrawn, so the card stays on the stale card.
   - **How to see it:** From a freshly loaded page, click "Next" once to show "2 + 2 = ?", then click "Shuffle" twice; the card still shows "2 + 2 = ?" because the screen never refreshed.
5. - **What changed:** the card's flip listener — it was attached to `innerEl` (the whole card) and is now attached to `frontEl` (the question face only).
   - **What goes wrong:** The card flips to the answer on the first click, but clicking it while the answer is facing you does nothing, so it stays stuck on the back until you navigate away.
   - **How to see it:** From a freshly loaded page, click the card to flip it, then click it again; it remains on the answer face, while a "Next" click brings it back to the front.