"""Draw `run.svg` from a real run of assay, so it matches the real output.

    python docs/hero.py bench/programs/opencode/gpt-oss-120b/58_reorder \
                        "assay ./reorder" docs/run.svg

The SVG animates like a terminal. The command is typed, the output rows
appear one at a time, the finished screen holds, and the animation loops.
Every row is drawn visible and the animation only hides rows until their
turn, so a viewer that doesn't animate, or a reader who prefers reduced
motion, sees the finished run.
"""
import html, pathlib, re, sys, textwrap
sys.path.insert(0, "src")
from assay import check

PAPER, DIM, TEXT, BRIGHT = "#12131a", "#6d7385", "#c6cad6", "#eef0f5"
GREEN, RED, AMBER = "#5ac37d", "#ef6b73", "#e2c15f"
#: Font size, line spacing, first baseline, left margin, bottom padding, and
#: the width of one character, in px. `ADVANCE` is a little above the font's
#: real character width, because the box is sized from it and a box narrower
#: than its text clips the longest row. `LEAD` gives a terminal's line height.
SIZE, LEAD, TOP, LEFT, PAD, ADVANCE = 17, 23, 50, 22, 18, 10.3
#: Where long lines wrap. GitHub scales a README image wider than about 830px
#: down, text included, so wrapping keeps the image under that and the text at
#: `SIZE`. Wrapped rows are indented under the text they continue.
COLUMNS = 76
#: Animation timings in seconds. Typing starts at `TYPE` with one key every
#: `KEY`. Output starts `WAIT` after the last key, with one line every `STEP`.
#: The finished screen holds for `HOLD`, then fades over `FADE` and the
#: animation loops.
TYPE, KEY, WAIT, STEP, HOLD, FADE = 0.3, 0.06, 1.0, 0.16, 1.4, 0.65


def wrap(line: str, hang: int) -> list[str]:
    return textwrap.wrap(line, COLUMNS, subsequent_indent=" " * hang,
                         break_on_hyphens=False) or [line]


def spans(line: str) -> list[str]:
    """Wrap one output line into SVG rows, coloured the way the terminal
    colours it."""
    esc = lambda s: html.escape(s, quote=False)
    tint = lambda colour, s: f'<tspan fill="{colour}">{esc(s)}</tspan>'
    if line.startswith(("    →", "    ↳")):
        colour = RED if line[4] == "→" else AMBER
        return [tint(colour, row) for row in wrap(line, 6)]
    # Matches plan cases (C001 up) and findings from outside the plan (F001
    # up, or C000 for the whole page).
    m = re.match(r"^([CF]\d+) \[(ok|FAILED|not checked)\] (.*)$", line)
    if not m:
        return [tint(BRIGHT, row) for row in wrap(line, 0)]
    ident, mark, what = m.groups()
    tone = {"ok": GREEN, "FAILED": RED, "not checked": AMBER}[mark]
    body = DIM if mark == "ok" else BRIGHT
    head = f"{ident} [{mark}] "
    first, *rest = wrap(line, len(head))
    return ([f'{tint(DIM, ident)} {tint(tone, f"[{mark}]")} '
             f'{tint(body, first[len(head):])}']
            + [tint(body, row) for row in rest])


def motion(command: str, lines: int) -> str:
    """The CSS animation that plays the run. Without it the SVG shows the
    finished run."""
    typed = len(command) * ADVANCE
    done = TYPE + len(command) * KEY
    answer = done + WAIT
    fade = answer + STEP * (lines - 1) + HOLD
    cycle = fade + FADE
    at = lambda seconds: f"{100 * seconds / cycle:.2f}%"
    keys = "\n".join(
        f"  @keyframes r{i}{{0%{{opacity:0}}{at(answer + STEP * i)},100%{{opacity:1}}}}"
        for i in range(lines))
    return f"""  <style>
  .play{{animation:fade {cycle:.2f}s linear infinite}}
  .row{{animation:{cycle:.2f}s step-end infinite}}
  .keys{{transform:translateX({typed:.1f}px);animation:type {cycle:.2f}s infinite}}
  .cursor{{opacity:0;animation:cursor {cycle:.2f}s step-end infinite}}
  @keyframes fade{{0%,{at(fade)}{{opacity:1}}100%{{opacity:0}}}}
  @keyframes type{{0%{{transform:translateX(0)}}
    {at(TYPE)}{{transform:translateX(0);animation-timing-function:steps({len(command)},end)}}
    {at(done)},100%{{transform:translateX({typed:.1f}px)}}}}
  @keyframes cursor{{0%{{opacity:1}}{at(answer)},100%{{opacity:0}}}}
{keys}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
  </style>"""


def draw(folder: str, command: str, out: pathlib.Path) -> None:
    run = check(folder)
    lines = [f"$ {command}", ""] + run.render().splitlines()
    rows = [f'    <text x="{LEFT}" y="{TOP}" xml:space="preserve">'
            f'<tspan fill="{GREEN}">$</tspan> '
            f'<tspan fill="{BRIGHT}">{html.escape(command)}</tspan>'
            f'</text>']
    # A terminal prints a wrapped line all at once, so all rows of one line
    # appear together.
    n, printed = 1, 0
    for line in lines[1:]:
        if not line:
            n += 1
            continue
        for row in spans(line):
            rows.append(f'    <text class="row" style="animation-name:r{printed}" '
                        f'x="{LEFT}" y="{TOP + LEAD * n}" '
                        f'xml:space="preserve">{row}</text>')
            n += 1
        printed += 1
    width = min(max(len(l) for l in lines), COLUMNS) * ADVANCE + LEFT * 2
    height = TOP + LEAD * (n - 1) + PAD + 12
    start = LEFT + 2 * ADVANCE
    rows.append(f'    <g class="keys">\n'
                f'      <rect x="{start}" y="{TOP - SIZE + 1}" '
                f'width="{len(command) * ADVANCE + 2:.0f}" height="{SIZE + 4}" '
                f'fill="{PAPER}"/>\n'
                f'      <rect class="cursor" x="{start}" y="{TOP - SIZE + 2}" '
                f'width="{ADVANCE:.0f}" height="{SIZE + 2}" fill="{TEXT}"/>\n'
                f'    </g>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
           f'height="{height:.0f}"\n'
           f'     viewBox="0 0 {width:.0f} {height:.0f}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace"\n'
           f'     font-size="{SIZE}">\n'
           + motion(command, printed) + "\n" +
           f'  <rect width="{width:.0f}" height="{height:.0f}" rx="10" '
           f'fill="{PAPER}"/>\n'
           f'  <circle cx="24" cy="22" r="6" fill="{RED}"/>\n'
           f'  <circle cx="44" cy="22" r="6" fill="{AMBER}"/>\n'
           f'  <circle cx="64" cy="22" r="6" fill="{GREEN}"/>\n'
           f'  <g class="play" fill="{TEXT}">\n' + "\n".join(rows)
           + "\n  </g>\n</svg>\n")
    out.write_text(svg)
    print(f"  {out}: {len(lines)} lines in {n} rows, {width:.0f}x{height:.0f}")
    print("  " + "\n  ".join(lines))


if __name__ == "__main__":
    draw(sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]))
