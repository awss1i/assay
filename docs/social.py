"""Draw `social-preview.png`, a 1280x640 card matched to the awssalmubarak.com
og card: a faint browser-window backdrop, the assay icon, a bold wordmark, and
a teal install line. The icon, wordmark baseline and sub-line are pinned to the
same positions as the site card so the two line up side by side.

    python docs/social.py docs/social-preview.png
"""
import pathlib, sys

PAGE, WHITE, TEAL, FAINT = "#0b0c11", "#eef0f5", "#6fd0c5", "#1a1c24"
SANS = "'Adwaita Sans','Inter','Noto Sans',sans-serif"
W, H = 1280, 640
ICON_SZ, ICON_TOP = 92, 191
WORD, WORD_TOP, WORD_FS = "assay", 294, 118
SUB, SUB_TOP, SUB_FS = "pip install assay-ui", 431, 30


def icon(sz: int) -> str:
    return (f'<svg viewBox="0 0 64 64" width="{sz}" height="{sz}">'
            f'<rect width="64" height="64" rx="14" fill="#111317"/>'
            f'<rect x="12" y="18" width="40" height="28" rx="4" fill="none" stroke="#eef0f4" stroke-width="3"/>'
            f'<line x1="12" y1="26" x2="52" y2="26" stroke="#eef0f4" stroke-width="3"/>'
            f'<circle cx="17.5" cy="22" r="1.7" fill="#eef0f4"/><circle cx="23.3" cy="22" r="1.7" fill="#eef0f4"/>'
            f'<path d="M28 30 L28 43.5 L31.7 40 L34.3 45.3 L36.4 44.3 L33.9 39.1 L38.6 38.8 Z" '
            f'fill="{TEAL}" stroke="#111317" stroke-width="1.6" stroke-linejoin="round"/></svg>')


def page() -> str:
    backdrop = (f'<svg style="position:absolute;inset:0" width="{W}" height="{H}">'
                f'<g stroke="{FAINT}" stroke-width="12" fill="none">'
                f'<rect x="980" y="-130" width="430" height="300" rx="30"/><line x1="980" y1="-66" x2="1410" y2="-66"/>'
                f'<rect x="-150" y="470" width="430" height="300" rx="30"/><line x1="-150" y1="534" x2="280" y2="534"/>'
                f'</g></svg>')
    center = "position:absolute;left:0;right:0;text-align:center"
    return (f'<!doctype html><meta charset="utf-8">'
            f'<style>html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{PAGE}}}</style>'
            f'{backdrop}'
            f'<div style="{center};top:{ICON_TOP}px">{icon(ICON_SZ)}</div>'
            f'<div style="{center};top:{WORD_TOP}px;font-family:{SANS};font-weight:800;font-size:{WORD_FS}px;'
            f'line-height:1;letter-spacing:-.03em;color:{WHITE}">{WORD}</div>'
            f'<div style="{center};top:{SUB_TOP}px;font-family:{SANS};font-weight:500;font-size:{SUB_FS}px;'
            f'line-height:1;color:{TEAL}">{SUB}</div>')


def render(out: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        tab.set_content(page())
        tab.wait_for_timeout(200)
        tab.screenshot(path=str(out))
        browser.close()
    print(f"  {out}: {W * 2}x{H * 2}")


if __name__ == "__main__":
    render(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/social-preview.png"))
