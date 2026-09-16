"""How an act reaches the page, with a page that only pretends.

What is checked here is which presses are attempted, not what they do, so a
stand-in page that records them is exact where a browser would only be slow.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

from assay.browser import perform


class Element:
    """A plain element: not a canvas, not disabled."""

    def evaluate(self, script: str) -> str:
        return "div"

    def get_attribute(self, name: str) -> None:
        return None


class Page:
    """A page on which every press times out, as on a covered control."""

    def __init__(self, present: bool) -> None:
        self.present = present
        self.pressed: List[str] = []
        self.mouse = SimpleNamespace(move=lambda x, y: None)

    def query_selector(self, selector: str):
        return Element() if self.present else None

    def click(self, selector: str, timeout: float, **where) -> None:
        self.pressed.append(selector)
        raise TimeoutError("Page.click: Timeout 4000ms exceeded.")

    def wait_for_timeout(self, ms: int) -> None:
        pass


def test_a_control_that_is_there_but_will_not_press_is_tried_once() -> None:
    """The back face of a flip card is on the page and under the front.

    The press times out, and retrying the selector as text can never match,
    because `text=#grid > div` is a search for those characters. One timeout
    per press, not two.
    """
    page = Page(present=True)

    could_not, _ = perform(page, [{"click": "#grid > div > .back"}])

    assert page.pressed == ["#grid > div > .back"]
    assert could_not and "Timeout" in could_not[0]


def test_words_that_name_no_element_are_tried_as_text() -> None:
    """`{"click": "Start"}` is what a person goes by, and it is not CSS."""
    page = Page(present=False)

    could_not, _ = perform(page, [{"click": "Start"}])

    assert page.pressed == ["Start", "text=Start"]
    assert could_not
