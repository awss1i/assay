"""Draw `social-preview.png` from a real run, for the same reason as `hero.py`.

    python docs/social.py bench/programs/dsh/gpt-oss-120b/30_paint2 \
                          "assay ./paint" docs/social-preview.png

GitHub wants 1280x640 and every card that shows it scales it down by two
or three, so the name and the tagline carry the message at that size and
the terminal carries the shape: green down the left, two red rows where
the page contradicted itself. The window sits flush to the left, as far
from the bottom edge as from the top. Long rows wrap at the window's edge,
which is what a terminal does with them. The text stops on a whole row, and
the rows are tight enough that both red ones fit.
"""
import html, pathlib, re, sys
sys.path.insert(0, "src")

PAPER, PAGE, EDGE = "#12131a", "#0b0c11", "#262938"
DIM, TEXT, BRIGHT = "#6d7385", "#c6cad6", "#eef0f5"
GREEN, RED, AMBER = "#5ac37d", "#ef6b73", "#e2c15f"
MONO = "'Adwaita Mono','JetBrains Mono','Liberation Mono',monospace"
SANS = "'Adwaita Sans','Inter','Noto Sans',sans-serif"
W, H = 1280, 640


def spans(line: str) -> str:
    """One rendered line, coloured the way the terminal colours it."""
    esc = lambda s: html.escape(s, quote=False)
    if line.startswith("$ "):
        return (f'<b style="color:{GREEN}">$</b> '
                f'<b style="color:{BRIGHT}">{esc(line[2:])}</b>')
    if line.startswith("    →"):
        return f'<span style="color:{RED}">{esc(line)}</span>'
    m = re.match(r"^(C\d+) \[(ok|FAILED|not checked)\] (.*)$", line)
    if not m:
        return f'<span style="color:{BRIGHT}">{esc(line)}</span>'
    ident, mark, what = m.groups()
    tone = {"ok": GREEN, "FAILED": RED, "not checked": AMBER}[mark]
    body = DIM if mark == "ok" else BRIGHT
    return (f'<span style="color:{DIM}">{ident}</span> '
            f'<span style="color:{tone}">[{mark}]</span> '
            f'<span style="color:{body}">{esc(what)}</span>')


def page(lines: list[str]) -> str:
    rows = "\n".join(spans(l) for l in lines)
    return f"""<!doctype html><meta charset="utf-8">
<style>
  html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{PAGE}}}
  .term{{position:absolute;left:48px;top:40px;width:772px;height:{H - 80}px;
         background:{PAPER};border:1px solid {EDGE};border-radius:12px;
         box-shadow:0 24px 60px rgba(0,0,0,.45)}}
  .dots{{padding:16px 20px 0;display:flex;gap:10px}}
  .dots i{{width:12px;height:12px;border-radius:50%}}
  pre{{margin:16px 0 0;padding:0 22px;font-family:{MONO};font-size:15px;
       line-height:18px;color:{TEXT};white-space:pre-wrap;overflow-wrap:anywhere;
       max-height:486px;overflow:hidden}}
  .side{{position:absolute;left:876px;right:48px;top:60px;font-family:{SANS};color:{BRIGHT}}}
  .side h1{{margin:0;font-size:64px;line-height:68px;font-weight:700;letter-spacing:-.02em}}
  .side p{{margin:14px 0 0;font-size:26px;line-height:35px;color:{TEXT}}}
  .side code{{display:block;margin-top:28px;font-family:{MONO};font-size:19px;color:{DIM}}}
</style>
<div class="term">
  <div class="dots"><i style="background:{RED}"></i><i style="background:{AMBER}"></i><i style="background:{GREEN}"></i></div>
<pre>{rows}</pre>
</div>
<div class="side">
  <h1>assay</h1>
  <p>find out if a generated web page actually works. no tests written, no LLM.</p>
  <code>pip install assay-ui</code>
</div>
"""


def render(lines: list[str], out: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        tab.set_content(page(lines))
        tab.wait_for_timeout(200)
        tab.screenshot(path=str(out))
        browser.close()
    print(f"  {out}: {W}x{H}")


def draw(folder: str, command: str, out: pathlib.Path) -> None:
    from assay import check
    run = check(folder)
    lines = [f"$ {command}", ""] + run.render().splitlines()
    render(lines, out)
    print("  " + "\n  ".join(lines))


if __name__ == "__main__":
    draw(sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]))
