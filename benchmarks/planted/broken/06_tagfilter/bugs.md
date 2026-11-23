1.
- **What changed:** In `filterItems`, the filtering loop now runs `for (let i = 0; i < children.length - 1; i++)` instead of `for (let i = 0; i < children.length; i++)`.
- **What goes wrong:** The last item (Item 12) is never hidden by any tag filter, so it stays on screen no matter which tags are selected.
- **How to see it:** Load the page and click the "red" tag button; Item 12 (tags green, medium, round) is still shown although it has no red tag.

2.
- **What changed:** In `filterItems`, the match test is now `const matches = itemTags.every(t => activeTags.has(t));` instead of `const matches = [...activeTags].every(t => itemTags.includes(t));`.
- **What goes wrong:** An item only matches if all of its own tags are selected, so clicking a tag hides even the items that carry that tag.
- **How to see it:** Load the page and click the "red" tag button; Items 1, 4, 7 and 10 all have the red tag, yet they all disappear and only the unrelated Item 12 remains.

3.
- **What changed:** In `filterItems`, the no-match note is now toggled with `noMatchP.classList.toggle('hidden', !anyVisible);` instead of `noMatchP.classList.toggle('hidden', anyVisible);`.
- **What goes wrong:** The "No items match the selected tags." note appears exactly when matching items are visible, and stays hidden when nothing matches.
- **How to see it:** Load the page, click the "red" tag, then click the "large" tag; Items 1 and 12 are visible, yet the "No items match the selected tags." note is shown at the same time.

4.
- **What changed:** In the tag-button click handler in `renderTagButtons`, `filterItems()` is now called only inside the branch that selects a tag; before, it was called unconditionally once after the if/else.
- **What goes wrong:** Deselecting a tag updates the selection and the button highlight but never re-filters the list, so the displayed items become stale.
- **How to see it:** Load the page, click "red", then click "large" (Items 1 and 12 and the no-match note are shown); now unclick "large" — the list does not change at all, it is identical to before the click, because deselecting a tag never redraws the items.

5.
- **What changed:** In `renderItems`, each tag chip is now created with `span.textContent = item.text;` instead of `span.textContent = t;`.
- **What goes wrong:** Every item's tag row shows the item's own name repeated once per tag instead of its actual tag names.
- **How to see it:** Load the page and look at the small tag row under any item; for example, Item 1 shows "Item 1 Item 1" where its tags "red large" should be.