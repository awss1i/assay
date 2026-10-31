"""Draw `social-preview.png`, the image GitHub shows in links to the repo.

    python docs/social.py docs/social-preview.png

The card has a gritty paper panel with the name, the language and the repo
description, and beside it a tilted ink panel with the first cases of a real
run of assay. The fonts are in `docs/fonts`, so the card draws the same on any
machine.
"""
import base64, html, pathlib, sys
sys.path.insert(0, "src")
from assay import check

PAPER, PAPER2, INK, ACCENT, NOTE = "#f2ede3", "#e7e0d2", "#15120f", "#ec6a1f", "#b9b1a2"
W, H = 1280, 640
FOLDER, COMMAND, CASES = "bench/programs/opencode/gpt-oss-120b/58_reorder", "assay ./reorder", 5
DESCRIPTION = "An agent-native QA CLI for web pages. Deterministic, no tests to write, no LLM."
FONTS = pathlib.Path(__file__).parent / "fonts"
#: Film grain over the whole card, and black grit on the paper panel only.
#: Both are SVG noise. The grit keeps only the peaks of the noise, so it shows
#: as sparse specks rather than a grey wash.
GRAIN = ("<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 .08 0 0 0 0 .07 0 0 0 0 .06 0 0 0 .55 0'/></filter>"
         "<rect width='300' height='300' filter='url(%23n)'/></svg>")
GRIT = ("<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
        "<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='3' seed='7' stitchTiles='stitch'/>"
        "<feColorMatrix values='0 0 0 0 .08 0 0 0 0 .07 0 0 0 0 .06 6 0 0 0 -3.5'/></filter>"
        "<rect width='240' height='240' filter='url(%23g)'/></svg>")


def face(family: str, file: str) -> str:
    data = base64.b64encode((FONTS / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{data}) format('woff2')}}"


def rows(output: str) -> str:
    """The command and the first `CASES` cases, coloured the way the run on
    awssalmubarak.com is: failures in orange, repeat notes dimmed."""
    out = [f'<div style="color:{PAPER}">$ {html.escape(COMMAND)}</div>']
    cases = 0
    for line in output.splitlines()[2:]:
        if line.startswith("C"):
            cases += 1
            if cases > CASES:
                break
        colour = ACCENT if "[FAILED]" in line or "→" in line else NOTE if "↳" in line else PAPER2
        out.append(f'<div style="color:{colour}">{html.escape(line)}</div>')
    return "".join(out)


def page(output: str) -> str:
    fonts = (face("Dela", "DelaGothicOne-Regular.woff2") + face("Mincho", "ShipporiMinchoB1-Bold.woff2")
             + face("Mono", "JetBrainsMono-Regular.woff2"))
    return f'''<!doctype html><meta charset="utf-8"><style>{fonts}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{PAPER};color:{INK};position:relative}}
.noise{{position:absolute;inset:0;pointer-events:none}}
</style>
<div style="position:absolute;left:44px;top:52px;width:440px;height:530px;background:{PAPER};
  border:3.4px solid {INK};transform:rotate(-.6deg);overflow:hidden">
  <div class="noise" style="opacity:.55;background-image:url(&quot;data:image/svg+xml;utf8,{GRIT}&quot;)"></div>
  <div style="position:absolute;left:44px;top:84px;font:100px/1 Dela;letter-spacing:-.01em">assay</div>
  <div style="position:absolute;left:46px;top:226px;background:{ACCENT};font:20px Dela;
    letter-spacing:.06em;padding:5px 12px">Python</div>
  <div style="position:absolute;left:46px;right:40px;top:296px;font:29px/1.32 Mincho">{DESCRIPTION}</div>
</div>
<div style="position:absolute;left:520px;top:40px;width:726px;height:560px;background:{INK};
  clip-path:polygon(0 0,100% 2.5%,100% 100%,1% 98.5%)">
  <div style="position:absolute;left:50px;right:20px;top:70px;height:470px;overflow:hidden;
    font:25px/1.62 Mono;white-space:pre;-webkit-mask-image:linear-gradient(#000 80%,#0000 100%)">{rows(output)}</div>
</div>
<div class="noise" style="opacity:.38;mix-blend-mode:multiply;
  background-image:url(&quot;data:image/svg+xml;utf8,{GRAIN}&quot;)"></div>'''


def render(out: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright
    # `check` runs its own Playwright, which can't nest inside this one.
    card = page(check(FOLDER).render())
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        tab.set_content(card)
        tab.evaluate("document.fonts.ready")
        tab.wait_for_timeout(300)
        # The noise is drawn at 2x so the grit stays fine, then saved at 1x,
        # because a 2x PNG of the grain is over GitHub's 1 MB limit.
        tab.screenshot(path=str(out), scale="css")
        browser.close()
    print(f"  {out}: {W}x{H}, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    render(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/social-preview.png"))
