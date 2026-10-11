"""Draw `report.png` from a real run of assay, so it matches the real report.

    python docs/report_shot.py bench/planted/broken/06_tagfilter \
                               docs/report.png

The script checks the program, writes the report the same way
`assay --report` does, opens it in a browser and screenshots the first
failing case as a reader first sees it. It uses the light theme because
GitHub shows the image on a light page, and twice the pixel density so it
stays sharp when GitHub scales it down.
"""
import pathlib
import sys
import tempfile

sys.path.insert(0, "src")
from playwright.sync_api import sync_playwright  # noqa: E402

from assay import check, report  # noqa: E402

#: Wide enough for the card to hold its two pictures side by side.
WIDTH = 960


def main(folder: str, out: str) -> int:
    with tempfile.TemporaryDirectory() as scratch:
        page_at = pathlib.Path(scratch) / "report.html"
        shots = pathlib.Path(scratch) / "report-shots"
        run = check(folder, shots=shots)
        report.write(run, page_at, folder=pathlib.Path(folder).name,
                     shots_dir=shots.name)
        first = next((r.case.id for r in run.failing), None)
        if first is None:
            print("nothing failed, so there is no failing case to show",
                  file=sys.stderr)
            return 1
        with sync_playwright() as p:
            browser = p.chromium.launch()
            view = browser.new_page(viewport={"width": WIDTH, "height": 900},
                                    device_scale_factor=2,
                                    color_scheme="light")
            view.goto(page_at.as_uri())
            view.wait_for_load_state("load")
            # The report lazy-loads its images and the failing case can be
            # far down the page, so every image is loaded before the shot.
            view.evaluate("""() => Promise.all([...document.images].map(
                (im) => { im.loading = 'eager';
                          return im.complete ? 1 : new Promise((done) => {
                              im.onload = im.onerror = done; }); }))""")
            card = view.locator(f"details.case#{first}")
            card.screenshot(path=out)
            browser.close()
    print(f"{out}: {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]))
