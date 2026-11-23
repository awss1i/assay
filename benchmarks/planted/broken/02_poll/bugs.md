# Planted bugs

1.
- **What changed:** The initial-load guard in the page script was `if(already!==null){` (show the saved results when the user has already voted); it is now `if(already===null){`.
- **What goes wrong:** A first-time visitor sees the results screen instead of the question, and a returning voter gets the question again instead of the results of their vote.
- **How to see it:** Load the page fresh: the results screen with "Change vote" is shown instead of the season question. Click "Change vote", select Spring, click Vote, then reload the page; the question is shown again instead of the results of the vote you just saved.

2.
- **What changed:** `showResults()` computed percentages with `votes.reduce((a,b)=>a+b,0) || 1;`; the `|| 1` fallback was removed, so the denominator is now `votes.reduce((a,b)=>a+b,0);`.
- **What goes wrong:** With no votes yet the percentages are computed as 0/0, so the Summer, Autumn and Winter bars read "NaN%" instead of 0%.
- **How to see it:** Load the page fresh, which immediately shows the results screen; the Summer, Autumn and Winter bars each read "NaN%".

3.
- **What changed:** `showResults()` drew every bar with `votes.forEach((cnt,i)=>{...});`; it now uses `for(let i=1;i<votes.length;i++){ const cnt = votes[i]; ... }`, skipping index 0.
- **What goes wrong:** The Spring bar is never drawn, so it stays blank and empty even when Spring has all the votes.
- **How to see it:** Load the page fresh, click "Change vote", select Spring, click Vote; the Summer, Autumn and Winter bars read 0% while the Spring bar is completely blank, even though it holds the only vote.

4.
- **What changed:** The Winter radio input was `<input type="radio" name="option" value="3">`; it is now `value="2"`, the same value as Autumn.
- **What goes wrong:** A vote for Winter lands in Autumn's tally, so the results show Autumn winning when Winter was chosen.
- **How to see it:** Load the page fresh, click "Change vote", select Winter, click Vote; the Autumn bar shows 100% while the Winter bar shows 0%.

5.
- **What changed:** `resetPoll()` cleared the old selection with `document.querySelectorAll('input[name="option"]')`; it now queries `'input[type="checkbox"]'`, which matches no element on this page.
- **What goes wrong:** "Change vote" brings the question back with the previous selection still checked, so clicking Vote again re-casts the old season by accident.
- **How to see it:** Load the page fresh, click "Change vote", select Summer, click Vote, then click "Change vote" again; the Summer radio is still checked.