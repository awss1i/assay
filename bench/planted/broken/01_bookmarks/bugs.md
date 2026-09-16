# Planted bugs

1.
- **What changed:** The Remove handler's removal in `render()` was `bookmarks.splice(i, 1)`; it is now `bookmarks.splice(i + 1, 1)`.
- **What goes wrong:** Clicking Remove deletes the next bookmark in the list instead of the one you clicked, and the last bookmark can never be removed.
- **How to see it:** Load the page, add two bookmarks (titled "A" and "B"), and click Remove on the "A" row; the "B" row disappears instead.

2.
- **What changed:** In `render()`, the Open link was set with `openLink.href = b.url`; it is now `openLink.href = b.title`.
- **What goes wrong:** The "Open" link navigates to the bookmark's title as a page path instead of the bookmark's URL.
- **How to see it:** Add a bookmark with title "Docs" and URL "https://example.com", then click its "Open" link; the new tab loads a 404 path ending in "Docs" rather than example.com.

3.
- **What changed:** In `loadBookmarks()`, the stored data was read with `localStorage.getItem(storageKey)` (the key "bookmarks"); it now reads `localStorage.getItem("bookmark")`, a key `saveBookmarks()` never writes.
- **What goes wrong:** Bookmarks are saved but never read back, so everything appears lost after a reload.
- **How to see it:** Add a bookmark and confirm it appears in the list, then reload the page; the list is empty and nothing was restored.

4.
- **What changed:** In `render()`, the counter was set with `countSpan.textContent = bookmarks.length`; it is now `countSpan.textContent = bookmarks.length - 1`.
- **What goes wrong:** The "Saved:" counter always shows one fewer than the bookmarks actually on the list, and shows -1 when there are none.
- **How to see it:** On a freshly loaded page the counter reads "Saved: -1"; add one bookmark and the counter reads "Saved: 0" while one bookmark is listed below it.

5.
- **What changed:** The required-field guard in `addBookmark()` was `if (!title || !url)`; it is now `if (!title && !url)`.
- **What goes wrong:** The "required" warning only fires when both fields are empty, so a bookmark can be saved with a blank title, and an entry with only a title is rejected as an "Invalid URL".
- **How to see it:** Leave the Title field empty, type "https://example.com" in the URL field, and click Save; no "required" alert appears and a bookmark with an empty title is added to the list.