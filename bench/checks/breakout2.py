"""Where the ball goes in both 36_breakout2 programs.

    python bench/checks/breakout2.py

Written to settle two `truth.txt` lines by driving the pages rather than by
reading them. Every `ctx.arc` call is recorded, which is how both programs
draw their ball, so the ball's centre can be followed frame by frame.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

from assay.browser import serve  # noqa: E402

PROGRAMS = Path(__file__).resolve().parents[1] / "programs"

#: Keeps the last few ball centres the page drew.
FOLLOW = """
(() => {
  window.__arcs = [];
  const arc = CanvasRenderingContext2D.prototype.arc;
  CanvasRenderingContext2D.prototype.arc = function (x, y, r, ...rest) {
    window.__arcs.push([Math.round(x), Math.round(y)]);
    if (window.__arcs.length > 400) window.__arcs.shift();
    return arc.call(this, x, y, r, ...rest);
  };
})();
"""


def follow(folder: Path, click_at: float, wait_ms: int = 1500) -> dict:
    """Click the canvas at a fraction of its width and follow the ball."""
    with serve(folder) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 760})
        page.add_init_script(FOLLOW)
        page.goto(f"{base}/index.html")
        page.wait_for_timeout(800)
        box = page.query_selector("canvas").bounding_box()
        x = box["x"] + box["width"] * click_at
        y = box["y"] + box["height"] * 0.9
        page.mouse.move(x, y)
        page.wait_for_timeout(200)
        before = page.evaluate("window.__arcs.slice(-1)[0]")
        page.mouse.click(x, y)
        page.wait_for_timeout(120)
        early = page.evaluate("window.__arcs.slice(-1)[0]")
        page.wait_for_timeout(wait_ms)
        late = page.evaluate("window.__arcs.slice(-1)[0]")
        text = page.inner_text("body")
        browser.close()
    return {"before": before, "just after the click": early,
            "later": late, "text": " ".join(text.split())[:160]}


def paddle_moves(folder: Path) -> bool:
    """Whether the bottom strip of the canvas changes as the pointer moves."""
    with serve(folder) as base, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 760})
        page.goto(f"{base}/index.html")
        page.wait_for_timeout(800)
        box = page.query_selector("canvas").bounding_box()
        strip = {"x": box["x"], "y": box["y"] + box["height"] - 30,
                 "width": box["width"], "height": 30}
        shots = []
        for at in (0.2, 0.8):
            page.mouse.move(box["x"] + box["width"] * at,
                            box["y"] + box["height"] * 0.9)
            page.wait_for_timeout(300)
            shots.append(page.screenshot(clip=strip))
        browser.close()
    return shots[0] != shots[1]


def main() -> int:
    for cell in ("no-harness", "opencode"):
        folder = PROGRAMS / cell / "gpt-oss-120b" / "36_breakout2"
        for at in (0.5, 0.15):
            print(f"{cell}, click at {at:.2f} of the width:",
                  follow(folder, at))
        print(f"{cell}, the paddle follows the pointer:", paddle_moves(folder))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
