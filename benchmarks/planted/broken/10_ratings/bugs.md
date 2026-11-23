1.
- **What changed:** The `value` attribute of the `star1` radio input in the star rating markup; before it was `value="1"`, now it is `value="0"`.
- **What goes wrong:** Picking the leftmost (1-star) option and submitting shows the "Please select a star rating." alert and the rating is not recorded, because 0 is treated as unselected.
- **How to see it:** Load the page fresh, click the leftmost star, click Submit, and observe the "Please select a star rating." alert with no entry added to Past Ratings.

2.
- **What changed:** In `updateAverage()`, the display line template previously interpolated the computed mean, `` `Average rating: ${avg}` ``; it now interpolates `sum` instead of `avg`.
- **What goes wrong:** The average line shows the total of all submitted ratings instead of their mean, e.g. "Average rating: 7" after submitting 4 and 3.
- **How to see it:** Load the page fresh, click the 4th star and submit, then click the 3rd star and submit, and read the average line, which says "Average rating: 7" where 3.5 is expected.

3.
- **What changed:** In `addEntry()`, the empty-star count in the stars string, previously `'☆'.repeat(5-rating)`; it is now `'☆'.repeat(6-rating)`.
- **What goes wrong:** Every Past Ratings row renders six star symbols instead of five, e.g. a 4-star rating shows as ★★★★☆☆.
- **How to see it:** Load the page fresh, select any star rating and submit, then count the star symbols in the new Past Ratings row, where six appear instead of five.

4.
- **What changed:** In the Submit click handler's form reset, `document.getElementById('comment').value = ''` became `document.getElementById('comment').value = selectedRating`.
- **What goes wrong:** After a successful submit the comment box is not cleared but is filled with the numeric rating that was just sent, e.g. "4".
- **How to see it:** Load the page fresh, type "great page" into the comment box, click the 4th star, click Submit, and see the text box now contains "4" instead of being empty.

5.
- **What changed:** The `for` attribute of the rightmost star's `<label>`, previously `for="star5"`; it is now `for="star4"`, so the label toggles the 4-star radio instead of the 5-star radio.
- **What goes wrong:** Clicking the rightmost (5th) star never selects it — the four stars to its left light up while the clicked star stays unselected — and submitting records a 4 instead of a 5.
- **How to see it:** Load the page fresh, click the rightmost star and move the mouse away, where only four stars remain gold and the clicked star is gray; submit and see a 4-star entry recorded.