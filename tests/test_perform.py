"""Tests for which presses `perform` attempts. A stand-in page records each
press, so these tests don't need a browser.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

from assay.browser import perform


class Element:
    """An element that isn't a canvas and isn't disabled."""

    def evaluate(self, script: str) -> str:
        return "div"

    def get_attribute(self, name: str) -> None:
        return None


class Page:
    """A page where every press times out, as it does on a covered control."""

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
    """A selector that matches a covered element, like the back face of a
    flip card, is pressed once. Retrying it as `text=#grid > div` would
    search for those characters and could only time out again.
    """
    page = Page(present=True)

    could_not, _ = perform(page, [{"click": "#grid > div > .back"}])

    assert page.pressed == ["#grid > div > .back"]
    assert could_not and "Timeout" in could_not[0]


def test_words_that_name_no_element_are_tried_as_text() -> None:
    """`{"click": "Start"}` matches no element as CSS, so it's retried as
    `text=Start`."""
    page = Page(present=False)

    could_not, _ = perform(page, [{"click": "Start"}])

    assert page.pressed == ["Start", "text=Start"]
    assert could_not
