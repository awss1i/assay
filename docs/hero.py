"""Draw `run.svg` from a real run, so the picture cannot drift from the tool.

    python docs/hero.py bench/programs/dsh/gpt-oss-120b/30_paint2 \
                        "assay ./paint" docs/run.svg

The one this replaces was drawn by hand, and by the time anybody looked it
showed colour the command did not print and a program that does not exist. A
picture at the top of a README is a claim about what the tool does, and the
same rule applies to it as to every number the benchmark publishes: produce
it by doing the thing, or it describes whatever was true the day somebody
typed it.
"""
import html, pathlib, re, sys
sys.path.insert(0, "src")
from assay import check

PAPER, DIM, TEXT, BRIGHT = "#12131a", "#6d7385", "#c6cad6", "#eef0f5"
GREEN, RED, AMBER = "#5ac37d", "#ef6b73", "#e2c15f"
#: Line spacing, and how wide one character is at `font-size: 13`.
#:
#: **The advance was 7.22 and a monospace character at 13px takes about
#: 7.8**, so the box was drawn narrower than the text inside it and the
#: longest line ran off the edge and was clipped. It is the error line that
#: goes first, because that is the longest thing this tool prints. 7.9 leaves
#: a little room: a box wider than its text costs nothing, and one narrower
#: than its text loses the sentence the picture is there to show.
#:
#: `LEAD` is 17 rather than 21 for a line height of 1.31, which is what a
#: terminal looks like. 21 was 1.6 and made the picture half as tall again
#: for nothing.
LEAD, TOP, LEFT, PAD, ADVANCE = 17, 46, 22, 18, 7.9


def spans(line: str) -> str:
    """One rendered line, coloured the way the terminal colours it."""
    esc = lambda s: html.escape(s, quote=False)
    if line.startswith("    →"):
        return f'<tspan fill="{RED}">{esc(line)}</tspan>'
    m = re.match(r"^(C\d+) \[(ok|FAILED|not checked)\] (.*)$", line)
    if not m:
        return f'<tspan fill="{BRIGHT}">{esc(line)}</tspan>'
    ident, mark, what = m.groups()
    tone = {"ok": GREEN, "FAILED": RED, "not checked": AMBER}[mark]
    body = DIM if mark == "ok" else BRIGHT
    return (f'<tspan fill="{DIM}">{ident}</tspan> '
            f'<tspan fill="{tone}">[{mark}]</tspan> '
            f'<tspan fill="{body}">{esc(what)}</tspan>')


def draw(folder: str, command: str, out: pathlib.Path) -> None:
    run = check(folder)
    lines = [f"$ {command}", ""] + run.render().splitlines()
    width = max(len(l) for l in lines) * ADVANCE + LEFT * 2
    height = TOP + LEAD * (len(lines) - 1) + PAD + 12
    rows = []
    for n, line in enumerate(lines):
        y = TOP + LEAD * n
        if n == 0:
            body = (f'<tspan fill="{GREEN}">$</tspan> '
                    f'<tspan fill="{BRIGHT}">{html.escape(command)}</tspan>')
        else:
            body = spans(line)
        if line:
            rows.append(f'    <text x="{LEFT}" y="{y}" '
                        f'xml:space="preserve">{body}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
           f'height="{height:.0f}"\n'
           f'     viewBox="0 0 {width:.0f} {height:.0f}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace"\n'
           f'     font-size="13">\n'
           f'  <rect width="{width:.0f}" height="{height:.0f}" rx="10" '
           f'fill="{PAPER}"/>\n'
           f'  <circle cx="24" cy="22" r="6" fill="{RED}"/>\n'
           f'  <circle cx="44" cy="22" r="6" fill="{AMBER}"/>\n'
           f'  <circle cx="64" cy="22" r="6" fill="{GREEN}"/>\n'
           f'  <g fill="{TEXT}">\n' + "\n".join(rows) + "\n  </g>\n</svg>\n")
    out.write_text(svg)
    print(f"  {out}: {len(lines)} lines, {width:.0f}x{height:.0f}")
    print("  " + "\n  ".join(lines))


if __name__ == "__main__":
    draw(sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]))
