"""Draw `run.svg` from a real run, so the picture cannot drift from the tool.

    python docs/hero.py bench/planted/broken/06_tagfilter \
                        "assay ./tags" docs/run.svg

The one this replaces was drawn by hand, and by the time anybody looked it
showed colour the command did not print and a program that does not exist. A
picture at the top of a README is a claim about what the tool does, and the
same rule applies to it as to every number the benchmark publishes: produce
it by doing the thing, or it describes whatever was true the day somebody
typed it.

It plays the run the way a terminal shows it: the command is typed, the rows
arrive one after another, the finished screen holds long enough to read, and
the cycle starts again. Everything is drawn visible and the animation only
hides it until its turn, so a viewer that does not animate, or a reader who
has asked for less motion, gets the finished run.
"""
import html, pathlib, re, sys, textwrap
sys.path.insert(0, "src")
from assay import check

PAPER, DIM, TEXT, BRIGHT = "#12131a", "#6d7385", "#c6cad6", "#eef0f5"
GREEN, RED, AMBER = "#5ac37d", "#ef6b73", "#e2c15f"
#: Font size, line spacing, and how wide one character is at that size.
#:
#: A monospace character at 15px takes about 9.0, and the box is sized from
#: `ADVANCE`, so 9.1 leaves a little room: a box wider than its text costs
#: nothing, and one narrower than its text clips the longest row.
#:
#: `LEAD` is 20 for a line height of 1.33, which is what a terminal looks
#: like.
SIZE, LEAD, TOP, LEFT, PAD, ADVANCE = 15, 20, 46, 22, 18, 9.1
#: Where long lines wrap. GitHub shows a README picture at most about 830px
#: wide and scales a wider one down, text and all. Unwrapped, the error line
#: makes the picture over 1300px wide and the text shows at about 9px; at 80
#: columns the picture fits and the text shows at `SIZE`. Lines break between
#: words and the rest is indented under the text, so a message reads as one.
COLUMNS = 80
#: Seconds: typing starts at `TYPE`, a key every `KEY`; the run answers
#: `WAIT` after the last key and prints a line every `STEP`; the finished
#: screen holds for `HOLD`, fades over `FADE`, and the cycle starts again.
TYPE, KEY, WAIT, STEP, HOLD, FADE = 0.3, 0.06, 1.0, 0.16, 1.4, 0.65


def wrap(line: str, hang: int) -> list[str]:
    return textwrap.wrap(line, COLUMNS, subsequent_indent=" " * hang,
                         break_on_hyphens=False) or [line]


def spans(line: str) -> list[str]:
    """One rendered line as the rows it wraps to, coloured the way the
    terminal colours it."""
    esc = lambda s: html.escape(s, quote=False)
    tint = lambda colour, s: f'<tspan fill="{colour}">{esc(s)}</tspan>'
    if line.startswith(("    →", "    ↳")):
        colour = RED if line[4] == "→" else AMBER
        return [tint(colour, row) for row in wrap(line, 6)]
    # A finding about the whole run is numbered F001 or C000, and is a
    # failure like any other.
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
    """The stylesheet that plays the run. Without it the picture is the end."""
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
    # A terminal prints a wrapped line all at once, so every row of one
    # line shares that line's turn.
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
