"""Draw `demo.mp4` from a real run, for the same reason as `hero.py`.

    python docs/demo.py bench/programs/dsh/gpt-oss-120b/30_paint2 \
                        "assay ./paint" docs/demo.mp4

Needs `ffmpeg` on PATH, or its path in `FFMPEG`.

It is cut for a post on X, where the feed plays video in a player about
540px wide. A terminal with 110-character rows was unreadable at that size
whatever the bitrate, so the text is sized to about 65 characters to a row.
A square frame read as well but took a whole screen of feed. At 16:9 the
window shows 15 rows, which for the paint run puts the first failure on the
top row of the finished screen.

The run scrolls the way a terminal does and stops on the last row, with
both red rows on screen. Passing rows are a lighter grey than the other
pictures use and the failures are bold, because X re-encodes every upload
and thin dim text on a dark ground is the first thing it smears. The bitrate
is fixed at 10 Mbps, above the 5 Mbps X asks for, so the copy it re-encodes
from is clean.
"""
import html, os, pathlib, re, subprocess, sys, tempfile
sys.path.insert(0, "src")

PAPER, PAGE, EDGE = "#12131a", "#0b0c11", "#262938"
DIM, TEXT, BRIGHT = "#8f95a8", "#c6cad6", "#eef0f5"
GREEN, RED, AMBER = "#5ac37d", "#ef6b73", "#e2c15f"
MONO = "'Adwaita Mono','JetBrains Mono','Liberation Mono',monospace"
W, H = 1920, 1080
#: Font size, line height, and how many rows the window shows.
SIZE, LEAD, ROWS = 46, 60, 15
#: Frames at `FPS`: the command alone, each printed row, the finished screen.
FPS, HOLD, STEP, END = 30, 15, 2, 75


def spans(line: str) -> str:
    """One rendered line, coloured the way the terminal colours it."""
    esc = lambda s: html.escape(s, quote=False)
    if line.startswith("$ "):
        return (f'<b style="color:{GREEN}">$</b> '
                f'<b style="color:{BRIGHT}">{esc(line[2:])}</b>')
    if line.startswith("    →"):
        return f'<b style="color:{RED}">{esc(line)}</b>'
    m = re.match(r"^(C\d+) \[(ok|FAILED|not checked)\] (.*)$", line)
    if not m:
        return f'<span style="color:{BRIGHT}">{esc(line)}</span>'
    ident, mark, what = m.groups()
    tone = {"ok": GREEN, "FAILED": RED, "not checked": AMBER}[mark]
    tag, body = ("span", DIM) if mark == "ok" else ("b", BRIGHT)
    return (f'<span style="color:{DIM}">{ident}</span> '
            f'<{tag} style="color:{tone}">[{mark}]</{tag}> '
            f'<{tag} style="color:{body}">{esc(what)}</{tag}>')


def page(lines: list[str]) -> str:
    rows = "\n".join(spans(l) for l in lines)
    return f"""<!doctype html><meta charset="utf-8">
<style>
  html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{PAGE}}}
  .term{{position:absolute;inset:40px;background:{PAPER};border:1px solid {EDGE};
         border-radius:16px}}
  .dots{{padding:20px 24px 0;display:flex;gap:12px}}
  .dots i{{width:16px;height:16px;border-radius:50%}}
  .rows{{margin-top:22px;height:{ROWS * LEAD}px;overflow:hidden}}
  pre{{margin:0;padding:0 26px;font-family:{MONO};font-size:{SIZE}px;
       line-height:{LEAD}px;color:{TEXT};white-space:pre-wrap;overflow-wrap:anywhere}}
</style>
<div class="term">
  <div class="dots"><i style="background:{RED}"></i><i style="background:{AMBER}"></i><i style="background:{GREEN}"></i></div>
  <div class="rows"><pre>{rows}</pre></div>
</div>
"""


def frames(lines: list[str], into: pathlib.Path) -> list[tuple[pathlib.Path, int]]:
    """One still per printed row, scrolled to the bottom, and how long it shows."""
    from playwright.sync_api import sync_playwright
    shown = [n for n in range(1, len(lines) + 1) if lines[n - 1]]
    stills = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, n in enumerate(shown):
            tab.set_content(page(lines[:n]))
            tab.evaluate("r => r.scrollTop = r.scrollHeight",
                         tab.query_selector(".rows"))
            path = into / f"f{i:03}.png"
            tab.screenshot(path=str(path))
            last = i == len(shown) - 1
            stills.append((path, END if last else HOLD if i == 0 else STEP))
        browser.close()
    return stills


def encode(stills: list[tuple[pathlib.Path, int]], out: pathlib.Path) -> None:
    listing = stills[0][0].parent / "frames.txt"
    listing.write_text("ffconcat version 1.0\n" + "".join(
        f"file '{p}'\nduration {n / FPS:.6f}\n" for p, n in stills)
        + f"file '{stills[-1][0]}'\n")
    subprocess.run([
        os.environ.get("FFMPEG", "ffmpeg"), "-v", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"fps={FPS},scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
        "-b:v", "10M", "-minrate", "10M", "-maxrate", "10M", "-bufsize", "20M",
        "-x264-params", "nal-hrd=cbr",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "128k", "-shortest",
        "-movflags", "+faststart", str(out)], check=True)


def draw(folder: str, command: str, out: pathlib.Path) -> None:
    from assay import check
    run = check(folder)
    lines = [f"$ {command}", ""] + run.render().splitlines()
    with tempfile.TemporaryDirectory() as tmp:
        stills = frames(lines, pathlib.Path(tmp))
        encode(stills, out)
    seconds = sum(n for _, n in stills) / FPS
    print(f"  {out}: {W}x{H}, {seconds:.1f}s, {len(stills)} stills")
    print("  " + "\n  ".join(lines))


if __name__ == "__main__":
    draw(sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]))
