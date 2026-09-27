"""Whether opencode's 42_wizard2 can be finished, driven through every step.

    python bench/checks/wizard2.py

Written to settle its `truth.txt` line by using the page rather than by
reading it: fill each step with valid values, press Next, and see what the
final Submit says.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

from assay.browser import serve  # noqa: E402

FOLDER = (Path(__file__).resolve().parents[1] / "programs" / "opencode"
          / "gpt-oss-120b" / "42_wizard2")


def main() -> int:
    said = []
    with serve(FOLDER) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("dialog", lambda d: (said.append(d.message), d.accept()))
        page.goto(f"{base}/index.html")
        page.fill("#name", "Ada Lovelace")
        page.fill("#email", "ada@example.com")
        page.click("#next1")
        page.fill("#street", "12 Analytical Way")
        page.fill("#city", "London")
        page.fill("#zip", "12345")
        page.click("#next2")
        on_step_three = page.is_visible("#submit")
        zip_error = page.inner_text("#err-zip")
        page.click("#submit")
        page.wait_for_timeout(300)
        browser.close()
    print("step two accepted 12345:", on_step_three, repr(zip_error))
    print("what Submit said:", said)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
