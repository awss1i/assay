"""The whole thing, against pages small enough to read in one screen.

These are the shapes assay was wrong about on real generated programs, boiled
down until nothing is left but the fault. They need a browser, so they skip
where there is not one rather than failing for a reason that is nothing to do
with the code.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

import pytest

from assay import check

def _no_browser() -> bool:
    """Whether chromium is here. Absent is a skip, never a failure."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return not pathlib.Path(p.chromium.executable_path).exists()
    except Exception:
        return True


pytestmark = pytest.mark.skipif(_no_browser(), reason="no browser installed")


def build(tmp_path: Path, body: str, script: str = "") -> Path:
    """One page, served from its own folder."""
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><head><title>t</title></head><body>"
        f"{body}"
        + (f'<script type="module" src="./app.js"></script>' if script else "")
        + "</body></html>", encoding="utf-8")
    if script:
        (tmp_path / "app.js").write_text(script, encoding="utf-8")
    return tmp_path


def test_a_page_that_works_passes_every_case(tmp_path: Path) -> None:
    """The half that matters most.

    A checker that cries wolf on correct code is worse than none, because
    whoever is holding it goes and edits something that was right.
    """
    folder = build(
        tmp_path,
        '<button id="go">Go</button><p id="out">nothing yet</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'pressed';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()
    assert len(run.plan) >= 2


def test_a_page_that_throws_on_load_fails_on_the_first_case(
        tmp_path: Path) -> None:
    """Where a broken generated page usually gives itself away."""
    folder = build(tmp_path, "<button id='go'>Go</button>",
                   "document.getElementById('nope').addEventListener("
                   "'click', () => {});\n")

    run = check(folder)

    assert not run.works
    first = run.results[run.plan[0].id]
    assert first.failed, run.render()
    assert "threw" in first.detail


def test_a_canvas_nobody_draws_into_is_caught(tmp_path: Path) -> None:
    """A canvas is an element like any other: present, sized, visible."""
    folder = build(tmp_path, '<canvas id="c" width="200" height="200"></canvas>',
                   "// draws nothing at all\n")

    run = check(folder)

    assert not run.works
    said = " ".join(r.detail for r in run.failing)
    assert "nothing drawn" in said or "did not respond" in said, run.render()


def test_a_canvas_that_answers_the_keyboard_passes(tmp_path: Path) -> None:
    """A game is not broken for ignoring a click.

    This is the case that scored a working snake 1 of 5 before the plan
    learned to press keys as well as click.
    """
    folder = build(tmp_path, '<canvas id="c" width="200" height="200"></canvas>',
                   "const x = document.getElementById('c').getContext('2d');\n"
                   "x.fillStyle = '#888'; x.fillRect(0, 0, 200, 200);\n"
                   "let n = 0;\n"
                   "addEventListener('keydown', () => {\n"
                   "  n += 7; x.fillStyle = '#111';\n"
                   "  x.fillRect(n % 150, 20, 20, 20);\n"
                   "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_button_with_no_visible_effect_is_not_a_failure(
        tmp_path: Path) -> None:
    """A palette swatch that sets a variable and shows no selection border
    changes nothing measurable and is not broken.

    The swatch sits beside a canvas, which is where a palette lives and is
    the whole reason it is allowed to be silent: what it stores is read by
    something. A page holding nothing but this button stores a colour that
    nobody ever paints with, and `test_a_page_that_answers_nothing_is_broken`
    is what says so.
    """
    folder = build(tmp_path,
                   '<button id="pick">Red</button>'
                   '<canvas id="c" width="200" height="200"></canvas>',
                   "let chosen = 'red';\n"
                   "const ctx = document.getElementById('c').getContext('2d');\n"
                   "document.getElementById('pick').addEventListener("
                   "'click', () => { chosen = 'red'; });\n"
                   "let down = false;\n"
                   "const c = document.getElementById('c');\n"
                   "c.addEventListener('mousedown', () => { down = true; });\n"
                   "window.addEventListener('mouseup', () => { down = false; });\n"
                   "c.addEventListener('mousemove', (e) => {\n"
                   "  if (!down) return;\n"
                   "  const r = c.getBoundingClientRect();\n"
                   "  ctx.fillStyle = chosen;\n"
                   "  ctx.fillRect(e.clientX - r.left, e.clientY - r.top, 8, 8);\n"
                   "});\n")

    run = check(folder)

    assert run.works, run.render()
    swatch = [r for r in run.results.values() if "Red" in r.case.what]
    assert swatch and not any(r.failed for r in swatch), run.render()


def test_a_page_that_answers_nothing_is_broken(tmp_path: Path) -> None:
    """Every control inert and nothing else on the page: there is no program.

    A single control is allowed to do nothing visible, because what it sets
    may be read by something else. When *nothing* on the page ever changes
    whatever is pressed, nothing is reading it. Three `+ Add` buttons wired
    to an empty handler passed every case this tool had before this rule.
    """
    folder = build(tmp_path,
                   '<button id="a">+ Add</button>'
                   '<button id="b">+ Add</button>'
                   '<button id="c">+ Add</button>',
                   "let held = null;\n"
                   "for (const id of ['a', 'b', 'c'])\n"
                   "  document.getElementById(id).addEventListener("
                   "'click', () => { held = id; });\n")

    run = check(folder)

    assert not run.works, run.render()
    assert "responds to anything" in run.render()


def test_the_page_verdict_stands_down_when_it_could_not_reach_everything(
        tmp_path: Path) -> None:
    """The twin of the test above, and the reason it needs one.

    Same shape: a page where everything assay pressed did nothing. The
    difference is that here the part which *does* work was never reachable,
    so the plan was a sample rather than the page. A sortable table wired to
    its three headers, driven by clicking twenty-four data cells, was called
    broken while it sorted perfectly. The count of cases cannot see that: the
    board above ran fourteen and deserved the verdict, this one ran a dozen
    and did not.
    """
    folder = build(tmp_path,
                   '<table><tr><th id="h">Name</th></tr>'
                   + "".join(f'<tr><td>row {i}</td></tr>' for i in range(6))
                   + '</table>',
                   "document.getElementById('h').style.cursor = 'pointer';\n"
                   "document.getElementById('h').addEventListener('click',"
                   " () => { document.title = 'sorted'; });\n")

    run = check(folder)

    assert "responds to anything" not in run.render(), run.render()


def test_a_page_that_offers_nothing_is_still_judged(tmp_path: Path) -> None:
    """Left over, never few, and this is the case that separates them.

    A script that dies on its first line leaves a page with almost no
    surface, which is not the same as a page whose surface assay failed to
    read. Nothing is unreached here because nothing is there, so the verdict
    must still be available: silencing it on smallness would excuse exactly
    the program it exists to catch.
    """
    folder = build(tmp_path,
                   '<h2>Sheet</h2><table id="grid"></table>'
                   '<button id="go">Recalculate</button>',
                   "document.getElementById('go').addEventListener("
                   "'click', () => { nothingDefinedAnywhere(); });\n")

    run = check(folder)

    assert not run.works, run.render()


def test_a_control_the_program_disabled_is_the_program_answering(
        tmp_path: Path) -> None:
    """A limit the page declared and enforced is not a page that is dead.

    A quantity box saying `max="10"` was filled with 25, the program clamped
    it and switched off `+`, which is the whole feature working. assay then
    pressed the disabled `+`, saw nothing move, and reported that nothing on
    the page is wired. It had already written *the program has that control
    disabled* into its own evidence.
    """
    folder = build(tmp_path,
                   '<input id="q" type="number" value="1" min="1" max="10">'
                   '<button id="up">+</button><p id="t">Total: 9.99</p>',
                   "const q = document.getElementById('q');\n"
                   "const up = document.getElementById('up');\n"
                   "function draw() {\n"
                   "  let v = Math.min(10, Math.max(1, Number(q.value) || 1));\n"
                   "  q.value = v;\n"
                   "  document.getElementById('t').textContent ="
                   " 'Total: ' + (v * 9.99).toFixed(2);\n"
                   "  up.disabled = v >= 10;\n"
                   "}\n"
                   "q.addEventListener('input', draw);\n"
                   "up.addEventListener('click', () => {"
                   " q.value = Number(q.value) + 1; draw(); });\n"
                   "draw();\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_button_that_is_merely_dead_is_still_caught(tmp_path: Path) -> None:
    """The twin. Nothing here is disabled, so nothing excuses the silence.

    Same shape as the page above, one attribute different: this `+` is live
    and wired to a handler that does nothing at all. Taking the page's word
    for `disabled` must not become taking its word for everything.
    """
    folder = build(tmp_path,
                   '<input id="q" type="number" value="1" min="1" max="10">'
                   '<button id="up">+</button><p id="t">Total: 9.99</p>',
                   "document.getElementById('up').addEventListener("
                   "'click', () => { let ignored = 1; });\n")

    run = check(folder)

    assert not run.works, run.render()


def test_a_canvas_that_answered_and_went_back_has_answered(
        tmp_path: Path) -> None:
    """Select, then deselect, and the canvas is where it started.

    A palette outlined the shape that was clicked, put the outline away when
    the next click landed on the background, and ended on exactly the pixel
    count it began with: 18540 to 19276 to 18540. The case brackets the whole
    sequence, so two correct answers read as none, and it was reported as a
    canvas that does not respond to what was aimed at it.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="300" height="200"></canvas>',
                   "const c = document.getElementById('c');\n"
                   "const x = c.getContext('2d');\n"
                   "let picked = false;\n"
                   "function draw() {\n"
                   "  x.clearRect(0, 0, 300, 200);\n"
                   "  x.fillStyle = '#c33'; x.fillRect(40, 40, 80, 60);\n"
                   "  if (picked) { x.lineWidth = 6; x.strokeStyle = '#000';\n"
                   "    x.strokeRect(36, 36, 88, 68); }\n"
                   "}\n"
                   "c.addEventListener('click', (e) => {\n"
                   "  const r = c.getBoundingClientRect();\n"
                   "  const px = e.clientX - r.left, py = e.clientY - r.top;\n"
                   "  picked = px > 40 && px < 120 && py > 40 && py < 100;\n"
                   "  draw();\n"
                   "});\n"
                   "draw();\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_canvas_that_answers_nothing_at_all_is_still_caught(
        tmp_path: Path) -> None:
    """The twin. Nothing here ever moves, so there is nothing to go back to.

    Answering and returning must not become an excuse for never answering:
    this canvas is painted once at load and no gesture touches it again.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="300" height="200"></canvas>',
                   "const x = document.getElementById('c').getContext('2d');\n"
                   "x.fillStyle = '#c33'; x.fillRect(40, 40, 80, 60);\n")

    run = check(folder)

    assert not run.works, run.render()


GAME = ("let x = 0, over = false;\nconst c = document.getElementById('c').getContext('2d');\nconst tick = setInterval(() => {\n  x += 20;\n  c.clearRect(0, 0, 300, 200);\n  c.fillStyle = '#2a2'; c.fillRect(x, 80, 20, 20);\n  if (x > 180) { over = true; clearInterval(tick);%s }\n}, 60);\n")


def test_a_finished_program_that_promised_nothing_owes_nothing(
        tmp_path: Path) -> None:
    """The twin, and the two pages are otherwise identical.

    Same loop, same wall, same silence afterwards. It never told anybody to
    press anything, so ignoring the keyboard is a program that ended, not a
    program that was never wired. Without this the tool is reporting its own
    timing: it waits for the canvas to go still before acting, and on a game
    that ends by itself, gone still is game over.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="300" height="200"></canvas>'
                   '<p id="msg"></p>',
                   """%s""" % (GAME % (" document.getElementById('msg')"
                                       ".textContent = 'Game Over';")))

    run = check(folder)

    assert run.works, run.render()


ROWS = '<ul id="l"><li draggable="true">Row 1</li><li draggable="true">Row 2</li><li draggable="true">Row 3</li><li draggable="true">Row 4</li></ul><p id="o"></p>'

WIRE = "const l = document.getElementById('l');\nlet held = null;\nconst show = () => document.getElementById('o').textContent = 'Order: ' + [...l.children].map(n => n.textContent).join(' ');\nl.addEventListener('dragstart', e => held = e.target);\nl.addEventListener('dragover', e => e.preventDefault());\nl.addEventListener('drop', e => { e.preventDefault();%s });\nshow();\n"


def test_a_list_that_reorders_by_dragging_is_driven_by_dragging(
        tmp_path: Path) -> None:
    """`draggable` rows were invisible, and mouse events do not move them.

    A reorder list offers nothing a click can work, so a surface built from
    clickable things saw an empty page and had nothing to say about it. And
    the fix is not a press-move-release: HTML5 drag and drop is its own event
    family, so synthetic mouse movement never raises `dragstart` and a
    working list measures as one that ignores being dragged.
    """
    folder = build(tmp_path, ROWS,
                   WIRE % (" if (held && held !== e.target)"
                           " l.insertBefore(held, e.target); show();"))

    run = check(folder)

    assert run.works, run.render()


def test_a_list_whose_drop_is_wired_to_nothing_is_caught(
        tmp_path: Path) -> None:
    """The twin: same rows, same handlers, and the drop does nothing.

    One generated list inserted a placeholder under the cursor that none of
    its handlers were attached to, so no `drop` ever fired and the order
    never changed. Being able to drive a thing is what makes it possible to
    find that out.
    """
    folder = build(tmp_path, ROWS, WIRE % " show();")

    run = check(folder)

    assert not run.works, run.render()


def test_a_resize_bar_that_freezes_after_one_drag_is_caught(
        tmp_path: Path) -> None:
    """A bar that moves once and then cannot be caught again.

    The second drag is what matters and it has to be measured alone: bracket
    both and the first one's success hides the second one's failure, which is
    exactly how a split pane whose divider was squeezed to zero width passed.
    """
    folder = build(tmp_path,
                   '<div id="box" style="display:flex;width:400px;height:100px">'
                   '<div id="a" style="width:180px;background:#ddd"></div>'
                   '<div id="bar" style="width:8px;background:#333;'
                   'cursor:col-resize"></div>'
                   '<div id="b" style="flex:1;background:#eee"></div></div>',
                   "let on = false;\n"
                   "document.getElementById('bar').addEventListener("
                   "'mousedown', () => on = true);\n"
                   "window.addEventListener('mouseup', () => on = false);\n"
                   "window.addEventListener('mousemove', (e) => {\n"
                   "  if (!on) return;\n"
                   "  const a = document.getElementById('a');\n"
                   "  const w = Math.max(20, Math.min(380, e.clientX));\n"
                   "  a.style.width = w + 'px';\n"
                   "  document.getElementById('bar').style.width = '0px';\n"
                   "});\n")

    run = check(folder)

    assert not run.works, run.render()


def test_a_canvas_cleared_to_a_colour_and_never_drawn_into_is_caught(
        tmp_path: Path) -> None:
    """Full of one colour is not full of a picture.

    Painted counts non-transparent pixels, which answers the question for a
    2d canvas, starting transparent, and gets it backwards for one cleared to
    an opaque colour. Three generated wireframe cubes drew twenty-four line
    indices every frame into a buffer that clipped every one away, and each
    measured 836,000 painted pixels out of 836,000: completely full, and
    showing nothing.

    The button matters. No single case demands that a canvas draw unless the
    page offers nothing else to press, so without a run-level view this page
    is asked nothing at all.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="240" height="160"></canvas>'
                   '<button id="go">Pause</button>',
                   "const x = document.getElementById('c').getContext('2d');\n"
                   "let on = true;\n"
                   "const go = document.getElementById('go');\n"
                   "go.addEventListener('click', () => {\n"
                   "  on = !on; go.textContent = on ? 'Pause' : 'Resume';\n"
                   "});\n"
                   "function frame() {\n"
                   "  x.fillStyle = '#1a1a1a'; x.fillRect(0, 0, 240, 160);\n"
                   "  requestAnimationFrame(frame);\n"
                   "}\n"
                   "frame();\n")

    run = check(folder)

    assert not run.works, run.render()
    assert "ever drawn into this canvas" in run.render(), run.render()


def test_a_stroke_on_a_transparent_canvas_is_a_picture(
        tmp_path: Path) -> None:
    """The twin, and the reason uniformity alone will not do.

    A 2d canvas is transparent until something is drawn, so only the ink is
    measured, and a black line is exactly as much a single colour as a flat
    clear is. Testing uniformity on its own reported two working drawing
    tools as canvases nobody had drawn on. What separates a clear from a
    stroke is that the clear covers every pixel.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="240" height="160"></canvas>'
                   '<button id="go">Clear</button>',
                   "const c = document.getElementById('c');\n"
                   "const x = c.getContext('2d');\n"
                   "let down = false;\n"
                   "x.strokeStyle = '#000'; x.lineWidth = 3;\n"
                   "c.addEventListener('mousedown', (e) => {\n"
                   "  const r = c.getBoundingClientRect();\n"
                   "  down = true; x.beginPath();\n"
                   "  x.moveTo(e.clientX - r.left, e.clientY - r.top);\n"
                   "});\n"
                   "c.addEventListener('mousemove', (e) => {\n"
                   "  if (!down) return;\n"
                   "  const r = c.getBoundingClientRect();\n"
                   "  x.lineTo(e.clientX - r.left, e.clientY - r.top);"
                   " x.stroke();\n"
                   "});\n"
                   "window.addEventListener('mouseup', () => down = false);\n"
                   "document.getElementById('go').addEventListener("
                   "'click', () => x.clearRect(0, 0, 240, 160));\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_dom_cell_recoloured_counts_as_the_page_changing(
        tmp_path: Path) -> None:
    """No canvas, no text change, no element added, only a style."""
    folder = build(
        tmp_path,
        '<table><tr><td id="cell" style="width:40px;height:40px"></td></tr>'
        '</table><button id="paint">Paint</button>',
        "document.getElementById('paint').addEventListener('click', () => {\n"
        "  document.getElementById('cell').style.backgroundColor = 'green';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_the_surface_names_every_control_uniquely(tmp_path: Path) -> None:
    """Two inputs with no id both rendered as the selector `input`, so a plan
    could not address them separately and drove the first one twice."""
    folder = build(tmp_path, "<input><input><button>Go</button>")

    from assay import look

    controls = look(folder).surface.controls
    selectors = [c.selector for c in controls if c.kind]

    assert len(selectors) == len(set(selectors)), selectors
    assert len([c for c in controls if c.kind == "text"]) == 2


def test_a_page_that_mounts_late_is_measured_after_it_mounts(
        tmp_path: Path) -> None:
    """The whole of D, in one page.

    `load` fires before a framework has rendered anything, so a fixed pause
    after it measures whatever happens to be on screen at that moment. This
    page shows one word for 1200ms and then the app. Measured early it offers
    nothing, which plans a single case asserting only that nothing threw, and
    and an empty page throws nothing, so a working app came back
    `1 case, 1 passed`.
    """
    folder = build(tmp_path, '<div id="root">Loading...</div>', """
        setTimeout(() => {
          document.getElementById('root').innerHTML =
            '<input id="q" placeholder="Filter">' +
            '<button id="go">Go</button>';
          document.getElementById('go').onclick =
            () => document.body.appendChild(document.createElement('p'))
                      .textContent = 'went';
        }, 1200);
    """)
    run = check(folder)

    assert len(run.plan) > 1, "the late-mounted controls were never seen"
    assert [c for c in run.plan if "Go" in c.what]
    assert run.works, run.render()


def test_a_page_that_renders_nothing_is_not_a_page_that_passes(
        tmp_path: Path) -> None:
    """A React component that returns null for ever throws nothing.

    It offers no controls, so the plan is one case that asserts only that
    nothing threw, which is true of an empty document. This came back
    `1 case, 1 passed, exit 0` about an app with nothing in it at all.
    """
    folder = build(tmp_path, '<div id="root"></div>', "/* never renders */")
    run = check(folder)

    assert not run.works
    assert "rendered nothing" in run.failing[0].detail


def test_a_grid_of_coloured_divs_is_not_a_blank_page(tmp_path: Path) -> None:
    """The guard on the check above, and the reason it needs one.

    A grid built from styled `div`s has no text, no image and no canvas, so
    nothing the blank check can see is on it, and it is a perfectly good
    program whose cells are clickable. Calling it dead would be a false
    failure of the exact kind that costs more than a missed bug.
    """
    folder = build(tmp_path, '<div id="g"></div>', """
        const g = document.getElementById('g');
        for (let i = 0; i < 9; i++) {
          const d = document.createElement('div');
          d.setAttribute('role', 'button');
          d.style.cssText = 'width:40px;height:40px;background:#333';
          d.onclick = () => { d.style.background = '#4ade80'; };
          g.appendChild(d);
        }
    """)
    run = check(folder)

    assert len(run.plan) > 1
    assert run.works, run.render()


def test_a_page_that_blinds_the_driver_is_not_a_page_that_failed(
        tmp_path: Path) -> None:
    """One generated calculator declares `function eval()`.

    That replaces the global the driver evaluates through, so every reading
    comes back empty, and the blank check then reported *the page rendered
    nothing* about a calculator that correctly computes 7 + 3 = 10. The
    instrument being out is not the program being broken, and this is the
    exact shape assay exists to refuse: a check that could not run reading
    like one that failed.
    """
    folder = build(tmp_path,
                   '<div id="d">0</div><button id="go">Go</button>',
                   "")
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><head><title>t</title></head><body>"
        '<div id="d">0</div><button id="go">Go</button>'
        "<script>function eval() { return 1; }"
        "document.getElementById('go').onclick = "
        "() => document.getElementById('d').textContent = '1';</script>"
        "</body></html>", encoding="utf-8")
    run = check(folder)

    assert not run.works is False or True          # not a verdict either way
    assert run.unchecked, "nothing was recorded as unmeasurable"
    assert "nothing could be read" in run.unchecked[0].detail
    assert not [r for r in run.results.values() if r.failed], \
        "an unreadable page was reported as a failure"


def test_a_drawing_canvas_is_not_broken_for_ignoring_clicks(
        tmp_path: Path) -> None:
    """It answers to press-move-release and to nothing else."""
    folder = build(tmp_path, '<canvas id="c" width="300" height="200"></canvas>', """
        const c = document.getElementById('c');
        const x = c.getContext('2d');
        let down = false;
        c.addEventListener('mousedown', e => { down = true; x.beginPath();
            x.moveTo(e.offsetX, e.offsetY); });
        c.addEventListener('mousemove', e => { if (!down) return;
            x.lineTo(e.offsetX, e.offsetY); x.stroke(); });
        addEventListener('mouseup', () => { down = false; });
    """)
    run = check(folder)

    assert run.works, run.render()


def test_a_page_whose_answer_lands_in_a_field_has_changed(
        tmp_path: Path) -> None:
    """A converter puts its answer in the other box and nowhere else.

    Not in the visible text, not in the styles, not on a canvas. The page
    signature covered all three and not the fields, so typing 100 and getting
    212 back registered as *nothing on the page changed at all*, about three
    programs, one in every harness, every one verified by hand to work.
    """
    folder = build(tmp_path,
                   '<input id="c" placeholder="celsius">'
                   '<input id="f" placeholder="fahrenheit">', """
        const c = document.getElementById('c'), f = document.getElementById('f');
        c.addEventListener('input', () => {
          f.value = c.value === '' ? '' : String(Number(c.value) * 9 / 5 + 32);
        });
    """)
    run = check(folder)

    assert run.works, run.render()


def test_a_button_wired_to_nothing_is_still_caught(tmp_path: Path) -> None:
    """The guard on the fix above.

    Putting fields in the signature makes *nothing changed* rarer, which
    could quietly make assay permissive, and the benchmark cannot detect
    that, because every program in it works. So: a form that takes what you
    type and does nothing with it must still fail.
    """
    folder = build(tmp_path,
                   '<input id="task" placeholder="Task">'
                   '<button id="add">Add</button><ul id="list"></ul>',
                   "document.getElementById('add').addEventListener("
                   "'click', () => {});")
    run = check(folder)

    assert not run.works, "a dead Add button passed"


def test_a_grid_of_plain_divs_is_not_an_empty_page(tmp_path: Path) -> None:
    """81 divs with one handler on their parent is a minesweeper.

    No text, no canvas, no button, and no `role` or `onclick` to see, but a
    listener cannot be read from outside. `cursor: pointer` can be, and it is
    the page saying *click this*, which is exactly the question being asked.
    """
    folder = build(tmp_path, '<div id="board"></div>', """
        const board = document.getElementById('board');
        for (let i = 0; i < 81; i++) {
          const cell = document.createElement('div');
          cell.style.cssText =
            'width:24px;height:24px;background:#bbb;cursor:pointer;'
            + 'display:inline-block';
          board.appendChild(cell);
        }
        board.addEventListener('click', e => {
          if (e.target !== board) e.target.style.background = '#eee';
        });
    """)
    run = check(folder)

    assert run.works, run.render()


def test_a_sheet_of_editable_cells_is_ready_once_it_is_drawn(
        tmp_path: Path) -> None:
    """A spreadsheet's cells are controls, so the page has arrived.

    The surface types into a `contentEditable` cell. Readiness has to count
    it too, or every open of the sheet waits out the settle ceiling.
    """
    folder = build(tmp_path, '<table id="sheet"></table>', """
        const sheet = document.getElementById('sheet');
        for (let r = 0; r < 5; r++) {
          const row = sheet.insertRow();
          for (let c = 0; c < 5; c++) {
            const cell = document.createElement('div');
            cell.contentEditable = true;
            cell.style.cssText = 'width:60px;height:20px';
            row.insertCell().appendChild(cell);
          }
        }
    """)

    from assay import look

    rest = look(folder).rest

    assert rest.quiet and rest.live, rest
    assert rest.ms < 5000, rest


def test_a_table_sorted_by_its_headers_is_ready_once_it_is_drawn(
        tmp_path: Path) -> None:
    """A header with a pointer cursor is a cell the surface clicks.

    Readiness has to sweep the same tags the surface does, `th` included, or
    a table whose only controls are its headers waits out the ceiling.
    """
    folder = build(tmp_path, '<table id="t"><thead><tr></tr></thead>'
                             '<tbody></tbody></table>', """
        const head = document.querySelector('#t thead tr');
        for (const name of ['Name', 'Age', 'Joined']) {
          const th = document.createElement('th');
          th.textContent = name;
          th.style.cursor = 'pointer';
          th.onclick = () => document.querySelector('#t tbody')
              .appendChild(document.createElement('tr'));
          head.appendChild(th);
        }
    """)

    from assay import look

    rest = look(folder).rest

    assert rest.quiet and rest.live, rest
    assert rest.ms < 5000, rest


def test_a_list_reordered_by_dragging_is_ready_once_it_is_drawn(
        tmp_path: Path) -> None:
    """A `draggable` row is a handle the surface drags, so it is a control."""
    folder = build(tmp_path, '<ul id="list"></ul>', """
        const list = document.getElementById('list');
        for (let i = 1; i <= 5; i++) {
          const li = document.createElement('li');
          li.textContent = 'Item ' + i;
          li.draggable = true;
          li.style.cursor = 'move';
          list.appendChild(li);
        }
    """)

    from assay import look

    rest = look(folder).rest

    assert rest.quiet and rest.live, rest
    assert rest.ms < 5000, rest


def test_a_canvas_filled_by_a_button_is_not_unresponsive(
        tmp_path: Path) -> None:
    """A chart is output. It draws when you press Add, not when you poke it.

    Clicking and dragging such a canvas proves nothing, and demanding paint
    from it called four working programs dead: a chart in every harness and
    a bouncing-balls canvas that has no balls until you add one.
    """
    folder = build(tmp_path,
                   '<canvas id="chart" width="200" height="120"></canvas>'
                   '<input id="n" value="5"><button id="add">Add</button>', """
        const x = document.getElementById('chart').getContext('2d');
        let bars = [];
        document.getElementById('add').addEventListener('click', () => {
          bars.push(Number(document.getElementById('n').value) || 5);
          x.clearRect(0, 0, 200, 120);
          bars.forEach((b, i) => x.fillRect(i * 22 + 4, 120 - b * 8, 18, b * 8));
        });
    """)
    run = check(folder)

    assert run.works, run.render()


def test_a_form_is_filled_before_its_button_is_pressed(
        tmp_path: Path) -> None:
    """A sign-up form is right to refuse while the password is empty.

    Filling one box and demanding the button respond asserts the program
    should accept a half-finished form. Every field of the widget is filled
    first, so the case asks for something the program can actually grant.
    """
    folder = build(tmp_path,
                   '<form id="f"><input id="e" type="email" placeholder="Email">'
                   '<input id="p" type="password" placeholder="Password">'
                   '<button id="go">Next</button></form><p id="out"></p>', """
        document.getElementById('f').addEventListener('submit', ev => {
          ev.preventDefault();
          const e = document.getElementById('e').value;
          const p = document.getElementById('p').value;
          document.getElementById('out').textContent =
            (e.includes('@') && p.length >= 6) ? 'Welcome' : '';
        });
    """)
    run = check(folder)

    assert run.works, run.render()


def test_a_game_that_animates_then_dies_is_not_answering(
        tmp_path: Path) -> None:
    """Movement during a case is not movement caused by the case.

    A snake that plays itself for a moment, dies, and ignores the key it
    tells you to press was passing on the strength of its own last frames.
    The canvas is brought to rest first, so what moves afterwards moved
    because of the acts.

    **The message on the screen is load-bearing, and for a long time it was
    only in a code comment here.** A program that ends by itself and then
    ignores the keyboard is a game that finished; this one puts `Press Space
    to restart` in front of a person and then does nothing about it, which is
    a dead control and the whole of the difference. The fixture said so in a
    `//` comment the page cannot render, so it was testing a silent page and
    describing a speaking one.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<p id="msg"></p>',
                   "const ctx = document.getElementById('c').getContext('2d');\n"
                   "let x = 0;\n"
                   "const t = setInterval(() => {\n"
                   "  ctx.fillStyle = '#000'; ctx.fillRect(x, 40, 8, 8);\n"
                   "  if ((x += 10) > 90) {\n"
                   "    clearInterval(t);\n"
                   "    document.getElementById('msg').textContent ="
                   " 'Game Over! Press Space to restart.';\n"
                   "  }\n"
                   "}, 60);\n"
                   "// and the restart key is wired to nothing at all\n")

    run = check(folder)

    assert not run.works, run.render()


def test_a_game_that_keeps_animating_is_left_alone(tmp_path: Path) -> None:
    """The twin of the case above, and the reason it is safe.

    A program still producing frames when the ceiling arrives is alive, and
    nothing about it can be attributed to a gesture, so it is not asked to
    answer one.
    """
    folder = build(tmp_path, '<canvas id="c" width="200" height="200"></canvas>',
                   "const ctx = document.getElementById('c').getContext('2d');\n"
                   "let x = 0;\n"
                   "setInterval(() => {\n"
                   "  ctx.clearRect(0, 0, 200, 200);\n"
                   "  ctx.fillStyle = '#000';\n"
                   "  ctx.fillRect((x = (x + 7) % 180), 40, 8, 8);\n"
                   "}, 60);\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_surface_that_takes_one_stroke_must_take_the_next(
        tmp_path: Path) -> None:
    """A painter that draws a line and then forgets how."""
    folder = build(tmp_path, '<canvas id="c" width="200" height="200"></canvas>',
                   "const el = document.getElementById('c');\n"
                   "const ctx = el.getContext('2d');\n"
                   "let down = false, ever = false;\n"
                   "el.addEventListener('mousedown', () => { down = true; });\n"
                   "window.addEventListener('mouseup', () => { down = false; });\n"
                   "el.addEventListener('mousemove', (e) => {\n"
                   "  if (!down || ever) return;\n"
                   "  const r = el.getBoundingClientRect();\n"
                   "  ctx.fillRect(e.clientX - r.left, e.clientY - r.top, 6, 6);\n"
                   "});\n"
                   "window.addEventListener('mouseup', () => { ever = true; });\n")

    run = check(folder)

    assert not run.works, run.render()
    assert "forgotten how to draw" in run.render()


def test_a_canvas_nobody_draws_on_is_asked_nothing(tmp_path: Path) -> None:
    """A chart exempts itself by not answering the first stroke.

    This is what makes the rule above need no policy about what kind of
    canvas it is looking at: the program sets its own baseline.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<button id="go">Plot</button>',
                   "const ctx = document.getElementById('c').getContext('2d');\n"
                   "document.getElementById('go').addEventListener('click',\n"
                   "  () => { ctx.fillRect(10, 10, 60, 60); });\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_control_that_answers_only_its_second_press_is_one_behind(
        tmp_path: Path) -> None:
    """An undo stack that stores the state *after* the change.

    Its first press restores what is already on screen and looks inert; the
    second gives back the stroke before last. Nothing here reads the word on
    the button. The two presses are identical and only one of them answers.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<button id="u">Undo</button>',
                   "const el = document.getElementById('c');\n"
                   "const ctx = el.getContext('2d');\n"
                   "const past = [];\n"
                   "let down = false;\n"
                   "el.addEventListener('mousedown', () => { down = true; });\n"
                   "el.addEventListener('mousemove', (e) => {\n"
                   "  if (!down) return;\n"
                   "  const r = el.getBoundingClientRect();\n"
                   "  ctx.fillRect(e.clientX - r.left, e.clientY - r.top, 6, 6);\n"
                   "});\n"
                   "window.addEventListener('mouseup', () => {\n"
                   "  if (!down) return;\n"
                   "  down = false;\n"
                   "  past.push(ctx.getImageData(0, 0, 200, 200));\n"
                   "});\n"
                   "document.getElementById('u').addEventListener('click', () => {\n"
                   "  if (past.length) ctx.putImageData(past.pop(), 0, 0);\n"
                   "});\n")

    run = check(folder)

    assert not run.works, run.render()
    assert "one behind" in run.render()


def test_a_control_that_answers_both_presses_is_left_alone(
        tmp_path: Path) -> None:
    """The same page with the stack kept before the change, which is correct."""
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<button id="u">Undo</button>',
                   "const el = document.getElementById('c');\n"
                   "const ctx = el.getContext('2d');\n"
                   "const past = [];\n"
                   "let down = false;\n"
                   "el.addEventListener('mousedown', () => {\n"
                   "  down = true;\n"
                   "  past.push(ctx.getImageData(0, 0, 200, 200));\n"
                   "});\n"
                   "el.addEventListener('mousemove', (e) => {\n"
                   "  if (!down) return;\n"
                   "  const r = el.getBoundingClientRect();\n"
                   "  ctx.fillRect(e.clientX - r.left, e.clientY - r.top, 6, 6);\n"
                   "});\n"
                   "window.addEventListener('mouseup', () => { down = false; });\n"
                   "document.getElementById('u').addEventListener('click', () => {\n"
                   "  if (past.length) ctx.putImageData(past.pop(), 0, 0);\n"
                   "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_prompt_is_answered_rather_than_dismissed(tmp_path: Path) -> None:
    """A board that asks for the card's title through `prompt`.

    Dismissing is not neutral. It answers *no* to everything, which is the
    answer that makes the feature not happen. Three working kanban boards
    measured as pages where no button does anything.
    """
    folder = build(tmp_path,
                   '<ul id="list"></ul><button id="add">+ Add</button>',
                   "document.getElementById('add').addEventListener('click', () => {\n"
                   "  const title = prompt('Card title');\n"
                   "  if (!title) return;\n"
                   "  const li = document.createElement('li');\n"
                   "  li.textContent = title;\n"
                   "  document.getElementById('list').appendChild(li);\n"
                   "});\n")

    run = check(folder)

    assert run.works, run.render()


WEBGL = """
const c = document.getElementById('gl');
const gl = c.getContext('webgl');
gl.clearColor(0.1, 0.1, 0.1, 1);
const vs = gl.createShader(gl.VERTEX_SHADER);
gl.shaderSource(vs, 'attribute vec2 p; void main(){ gl_Position = vec4(p,0,1); }');
gl.compileShader(vs);
const fs = gl.createShader(gl.FRAGMENT_SHADER);
gl.shaderSource(fs, 'void main(){ gl_FragColor = vec4(0.9,0.3,0.1,1); }');
gl.compileShader(fs);
const pr = gl.createProgram();
gl.attachShader(pr, vs); gl.attachShader(pr, fs); gl.linkProgram(pr);
gl.useProgram(pr);
gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
const loc = gl.getAttribLocation(pr, 'p');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
let x = %s;
function frame() {
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(
    [x, -0.5, x + 0.6, -0.5, x + 0.3, 0.5]), gl.STATIC_DRAW);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  requestAnimationFrame(frame);
}
frame();
%s
"""


def test_a_webgl_canvas_can_be_measured_at_all(tmp_path: Path) -> None:
    """A 3D canvas answers `getContext('2d')` with null, and every canvas
    rule here reads pixels through one.

    Left alone, that is not a wrong measurement but no measurement: painted
    comes back -1, nothing is ever seen to change, and a 3D program is
    invisible to this tool. The read goes through `toDataURL` inside a frame
    callback instead, because outside one the drawing buffer has already been
    cleared and returns an image identical to a blank canvas.
    """
    folder = build(tmp_path, '<canvas id="gl" width="200" height="150"></canvas>',
                   WEBGL % ("-0.5", "window.addEventListener('keydown', e => {\n"
                                    "  if (e.key === 'ArrowRight') x += 0.3;\n"
                                    "  if (e.key === 'ArrowLeft') x -= 0.3;\n"
                                    "});"))

    run = check(folder)

    assert run.works, run.render()
    seen = " ".join(r.evidence for r in run.results.values())
    assert "-1" not in seen, f"the canvas was never read: {seen}"


def test_a_webgl_program_that_answers_nothing_is_caught(tmp_path: Path) -> None:
    """The twin: the same page with its keys wired to nothing.

    Without a readable canvas this passes, because a measurement that never
    comes back cannot disagree with anything. It is the case that proves the
    reading above is doing work rather than merely not crashing.
    """
    folder = build(tmp_path, '<canvas id="gl" width="200" height="150"></canvas>',
                   WEBGL % ("-0.5", "// nothing is wired to anything"))

    run = check(folder)

    assert not run.works, run.render()


def test_a_control_that_starts_something_slow_is_not_inert(
        tmp_path: Path) -> None:
    """A button whose work takes seconds still answered.

    Every case measures a moment after it acts, which is right for a button
    that responds at once and wrong for one that begins a two-second load.
    One page here shows an error and a Retry, and Retry starts exactly that:
    inside the window a case allows, the page looks like it answers nothing
    at all, and the whole program was called dead. The rule that makes that
    accusation is the one that waits longest before making it.
    """
    folder = build(tmp_path, '<button id="go">Retry</button><ul id="out"></ul>',
                   "document.getElementById('go').addEventListener('click', () => {\n"
                   "  setTimeout(() => {\n"
                   "    const li = document.createElement('li');\n"
                   "    li.textContent = 'loaded';\n"
                   "    document.getElementById('out').appendChild(li);\n"
                   "  }, 2000);\n"
                   "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_box_that_refuses_its_own_example_is_caught(tmp_path: Path) -> None:
    """A postcode whose `pattern` carries an escaped backslash.

    `\\\\d{5}` matches a literal backslash followed by five letter d's, so no
    postcode passes and a form requiring it can never be completed. Nothing
    that drives the page can find this: the field lives on a later step of a
    wizard, never on screen to be typed into, and every step before it
    advances perfectly. What settles it is that the page's own example and
    the page's own rule disagree.
    """
    folder = build(tmp_path,
                   '<form><label>Name<input name="who" required></label>'
                   '<label>Postcode<input name="zip" required '
                   'pattern="\\\\d{5}" placeholder="12345"></label>'
                   '<button id="go">Next</button></form>',
                   "document.getElementById('go').addEventListener('click',"
                   " (e) => { e.preventDefault(); });\n")

    run = check(folder)

    assert not run.works, run.render()
    assert "12345" in run.render() and "cannot be completed" in run.render()


def test_a_pattern_its_example_satisfies_is_left_alone(tmp_path: Path) -> None:
    """The twin, and the reason the rule is safe.

    The same page with the backslash written correctly. A working pattern
    must never be reported, and neither must a placeholder that is an
    instruction rather than an example: `Enter your postcode` matches no
    pattern and proves nothing, so a box carrying one is skipped.
    """
    folder = build(tmp_path,
                   '<form><label>Postcode<input name="zip" required '
                   'pattern="\\d{5}" placeholder="12345"></label>'
                   '<label>Phone<input name="tel" required '
                   'pattern="\\d{3}-\\d{4}" placeholder="Enter your number">'
                   '</label><button id="go">Next</button></form>'
                   '<p id="said"></p>',
                   "document.getElementById('go').addEventListener('click',"
                   " (e) => { e.preventDefault();\n"
                   "  document.getElementById('said').textContent ="
                   " 'step ' + (document.getElementById('said').textContent"
                   "            .replace('step ','') * 1 + 1); });\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_value_the_page_worked_out_by_mistake_is_caught(
        tmp_path: Path) -> None:
    """`NaN` on screen is arithmetic on something that was not a number.

    Nobody types it. A poll dividing by a total of zero showed `NaN%` beside
    every option and every case passed, because the text was there and it
    changed when asked to.
    """
    folder = build(
        tmp_path,
        '<button id="go">Total</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 0 / 0 + '%';\n"
        "});\n")

    run = check(folder)

    assert not run.works, run.render()
    assert any("NaN" in r.detail for r in run.failing), run.render()


def test_a_page_that_writes_those_words_on_purpose_is_left_alone(
        tmp_path: Path) -> None:
    """The twin, and the reason `null` is not one of the words checked.

    A page is allowed to be *about* these values. What it may not do is
    print one where a number belongs, and nothing here can tell those apart
    except that the word arrived as prose rather than as a value.
    """
    folder = build(
        tmp_path,
        '<p>A database row with no value stores null.</p>'
        '<button id="go">Go</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'done';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_two_choices_carrying_one_value_are_caught(tmp_path: Path) -> None:
    """One of them can never be the answer, and the markup is perfect.

    A poll whose Winter radio carried Autumn's value recorded every vote for
    Winter against Autumn. Both render, both are clickable, and every case
    passed.
    """
    folder = build(
        tmp_path,
        '<label><input type="radio" name="pick" value="1"> One</label>'
        '<label><input type="radio" name="pick" value="1"> Two</label>'
        '<button id="go">Go</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'done';\n"
        "});\n")

    run = check(folder)

    assert not run.works, run.render()
    assert any("can never be the answer" in r.detail
               for r in run.failing), run.render()


def test_choices_with_their_own_values_are_left_alone(tmp_path: Path) -> None:
    """The twin. Two groups may reuse a value; one group may not."""
    folder = build(
        tmp_path,
        '<label><input type="radio" name="a" value="1"> One</label>'
        '<label><input type="radio" name="a" value="2"> Two</label>'
        '<label><input type="radio" name="b" value="1"> Red</label>'
        '<label><input type="radio" name="b" value="2"> Blue</label>'
        '<button id="go">Go</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'done';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_label_pointing_at_nothing_is_caught(tmp_path: Path) -> None:
    """Clicking its words does nothing, and the page looks perfect.

    A rating widget whose fifth star carried the fourth star's `for` meant
    the top rating could never be chosen, and nothing else on the page said
    so.
    """
    folder = build(
        tmp_path,
        '<label for="ghost">Pick</label><input id="real" type="checkbox">'
        '<button id="go">Go</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'done';\n"
        "});\n")

    run = check(folder)

    assert not run.works, run.render()
    assert any("not on the page" in r.detail
               for r in run.failing), run.render()


def test_labels_that_point_at_their_own_controls_are_left_alone(
        tmp_path: Path) -> None:
    """The twin, including a label that wraps its input and needs no `for`."""
    folder = build(
        tmp_path,
        '<label for="one">One</label><input id="one" type="checkbox">'
        '<label>Two <input id="two" type="checkbox"></label>'
        '<button id="go">Go</button><p id="out">ready</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'done';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_slider_is_moved_rather_than_counted_as_surface(
        tmp_path: Path) -> None:
    """A page of sliders was reported as answering nothing at all.

    `range` counted as something the page offers and no case ever drove one,
    so a working colour mixer met the whole-page verdict: plenty on offer,
    none of it operated, nothing observed to change.
    """
    folder = build(
        tmp_path,
        '<input id="r" type="range" min="0" max="255" value="0">'
        '<p id="out">0</p>',
        "document.getElementById('r').addEventListener('input', (e) => {\n"
        "  document.getElementById('out').textContent = e.target.value;\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()
    assert any("move" in c.what for c in run.plan), run.render()



def test_a_square_one_behind_its_own_clicks_is_caught(
        tmp_path: Path) -> None:
    """A scheduler whose booked styling was inverted.

    Click a slot and it stays plain; click it again and it looks booked. The
    page moved both times, because a summary line followed each click, so
    every case passed. What the page cannot explain is the square answering
    the second press and not the first.
    """
    cells = "".join(
        f'<div class="cell" id="c{n}" style="cursor:pointer;'
        f'width:40px;height:40px;border:1px solid #333">{n}</div>'
        for n in range(6))
    folder = build(
        tmp_path, f'<div>{cells}</div><p id="log">nothing yet</p>', """
        const on = {};
        document.querySelectorAll('.cell').forEach((el) => {
          el.addEventListener('click', () => {
            on[el.id] = !on[el.id];
            el.classList.toggle('lit', !on[el.id]);
            document.getElementById('log').textContent =
                'booked ' + Object.keys(on).filter(k => on[k]).length;
          });
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("one behind" in r.detail for r in run.failing), run.render()


def test_a_square_that_answers_elsewhere_every_time_is_left_alone(
        tmp_path: Path) -> None:
    """The twin, and the reason the rule is about disagreement.

    A gallery thumbnail opens a lightbox and never changes itself. Both
    presses leave it exactly as it was, which is consistent and correct, and
    an earlier version of this rule called every thumbnail on the page a
    fault.
    """
    cells = "".join(
        f'<div class="cell" id="c{n}" style="cursor:pointer;'
        f'width:40px;height:40px;border:1px solid #333">{n}</div>'
        for n in range(6))
    folder = build(
        tmp_path,
        f'<div>{cells}</div><div id="box" hidden><p id="shown">none</p></div>',
        """
        document.querySelectorAll('.cell').forEach((el) => {
          el.addEventListener('click', () => {
            document.getElementById('box').hidden = false;
            document.getElementById('shown').textContent = el.id;
          });
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_a_control_that_never_answers_while_its_opposite_always_does(
        tmp_path: Path) -> None:
    """A deck whose Previous is wired to a condition that cannot be true.

    Pressing Previous on a freshly loaded deck does nothing and is right to,
    so the press that settles it is the one straight after Next.
    """
    folder = build(
        tmp_path,
        '<p id="card">1</p><button id="p">Previous</button>'
        '<button id="n">Next</button>',
        """
        let at = 1;
        const show = () => document.getElementById('card').textContent = at;
        document.getElementById('n').addEventListener('click', () => {
          if (at < 6) { at++; show(); }
        });
        document.getElementById('p').addEventListener('click', () => {
          if (at < 0) { at--; show(); }
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("never changed it once" in r.detail
               for r in run.failing), run.render()


def test_an_opposite_that_answers_after_its_pair_is_left_alone(
        tmp_path: Path) -> None:
    """The twin. Previous does nothing at the start and everything after."""
    folder = build(
        tmp_path,
        '<p id="card">1</p><button id="p">Previous</button>'
        '<button id="n">Next</button>',
        """
        let at = 1;
        const show = () => document.getElementById('card').textContent = at;
        document.getElementById('n').addEventListener('click', () => {
          if (at < 6) { at++; show(); }
        });
        document.getElementById('p').addEventListener('click', () => {
          if (at > 1) { at--; show(); }
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_a_toggle_that_goes_back_while_the_page_does_not(
        tmp_path: Path) -> None:
    """A tag filter whose second click clears the tag and not the filter."""
    tags = "".join(
        f'<span class="tag" id="t{n}" style="cursor:pointer;padding:4px;'
        f'border:1px solid #333">tag{n}</span>' for n in range(4))
    rows = "".join(f'<li class="row">item {n}</li>' for n in range(6))
    folder = build(
        tmp_path, f'<div>{tags}</div><ul>{rows}</ul>', """
        document.querySelectorAll('.tag').forEach((el) => {
          el.addEventListener('click', () => {
            const on = el.classList.toggle('lit');
            if (on) {
              document.querySelectorAll('.row').forEach((r, i) => {
                r.style.display = i % 2 ? 'none' : '';
              });
            }
          });
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("still done" in r.detail for r in run.failing), run.render()


def test_a_toggle_that_puts_the_page_back_too_is_left_alone(
        tmp_path: Path) -> None:
    """The twin: switching a filter off restores what it hid."""
    tags = "".join(
        f'<span class="tag" id="t{n}" style="cursor:pointer;padding:4px;'
        f'border:1px solid #333">tag{n}</span>' for n in range(4))
    rows = "".join(f'<li class="row">item {n}</li>' for n in range(6))
    folder = build(
        tmp_path, f'<div>{tags}</div><ul>{rows}</ul>', """
        document.querySelectorAll('.tag').forEach((el) => {
          el.addEventListener('click', () => {
            const on = el.classList.toggle('lit');
            document.querySelectorAll('.row').forEach((r, i) => {
              r.style.display = (on && i % 2) ? 'none' : '';
            });
          });
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_a_number_counting_the_list_that_disagrees_with_it(
        tmp_path: Path) -> None:
    """A bookmark manager whose counter reads one fewer than its rows.

    The page says which number is about the list by moving them together:
    this one changes by one every time a row arrives, so it plainly is the
    count. What it cannot be is minus one when there is nothing to count.
    """
    folder = build(
        tmp_path,
        '<input id="t" placeholder="Title"><button id="add">Add</button>'
        '<p>Saved: <span id="n">-1</span></p><div id="list"></div>', """
        const list = document.getElementById('list');
        let rows = 0;
        document.getElementById('add').addEventListener('click', () => {
          const box = document.createElement('div');
          box.className = 'row';
          box.textContent = document.getElementById('t').value || 'untitled';
          list.appendChild(box);
          rows++;
          document.getElementById('n').textContent = rows - 1;
          document.getElementById('t').value = '';
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("counting it" in r.detail for r in run.failing), run.render()


def test_a_number_that_counts_the_list_correctly_is_left_alone(
        tmp_path: Path) -> None:
    """The twin. The same page, counting properly."""
    folder = build(
        tmp_path,
        '<input id="t" placeholder="Title"><button id="add">Add</button>'
        '<p>Saved: <span id="n">0</span></p><div id="list"></div>', """
        const list = document.getElementById('list');
        let rows = 0;
        document.getElementById('add').addEventListener('click', () => {
          const box = document.createElement('div');
          box.className = 'row';
          box.textContent = document.getElementById('t').value || 'untitled';
          list.appendChild(box);
          rows++;
          document.getElementById('n').textContent = rows;
          document.getElementById('t').value = '';
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_something_typed_in_and_accepted_that_never_appears(
        tmp_path: Path) -> None:
    """A bookmark whose Open link points at the title instead of the URL.

    The row arrives, so the page accepted the entry; the address is simply
    nowhere on it, in the text, the boxes or the attributes.
    """
    folder = build(
        tmp_path,
        '<div><input id="t" placeholder="Title">'
        '<input id="u" placeholder="URL">'
        '<button id="add">Save</button></div><div id="list"></div>', """
        document.getElementById('add').addEventListener('click', () => {
          const row = document.createElement('div');
          row.className = 'row';
          const a = document.createElement('a');
          a.href = document.getElementById('t').value;
          a.textContent = 'Open';
          row.textContent = document.getElementById('t').value + ' ';
          row.appendChild(a);
          document.getElementById('list').appendChild(row);
          document.getElementById('t').value = '';
          document.getElementById('u').value = '';
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("does not carry it" in r.detail
               for r in run.failing), run.render()


def test_a_form_that_refuses_what_it_was_given_is_left_alone(
        tmp_path: Path) -> None:
    """The twin. A form that validates and adds nothing owes nothing.

    And the sharper case this rule was narrowed for: a sign-up form takes an
    address and a password, says *Account created*, and shows neither, which
    is correct and in the password's case required. Asking only whether the
    page had grown reported exactly that form.
    """
    folder = build(
        tmp_path,
        '<div><input id="t" placeholder="Title">'
        '<input id="u" placeholder="URL">'
        '<button id="add">Save</button></div><p id="msg">ready</p>'
        '<div id="list"></div>', """
        document.getElementById('add').addEventListener('click', () => {
          const u = document.getElementById('u').value;
          if (!u.startsWith('ftp://')) {
            document.getElementById('msg').textContent = 'needs an ftp link';
            return;
          }
          const row = document.createElement('div');
          row.className = 'row';
          row.textContent = u;
          document.getElementById('list').appendChild(row);
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_a_form_that_stores_what_it_takes_is_left_alone(
        tmp_path: Path) -> None:
    """The case this rule was narrowed for.

    A sign-up form takes an address and a password, says *Account created*,
    and shows neither. That is correct, and for the password it is required.
    The rule asks the list, not the page, and a form like this has no list.
    """
    folder = build(
        tmp_path,
        '<div><input id="e" placeholder="Email">'
        '<input id="p" type="password" placeholder="Password">'
        '<button id="go">Create Account</button></div><p id="msg">ready</p>',
        """
        document.getElementById('go').addEventListener('click', () => {
          const e = document.getElementById('e').value;
          document.getElementById('msg').textContent =
              e.includes('@') ? 'Account created' : 'that is not an address';
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_a_row_that_goes_is_the_one_you_pressed(tmp_path: Path) -> None:
    """A list splicing at the wrong index.

    Every count is right and the page changes exactly as much as it should:
    one row arrived, one row went. The wrong one went. It takes two rows on
    screen, holding different things, to see that at all, which is why the
    plan fills the page in first and types something different the second
    time.
    """
    folder = build(
        tmp_path,
        '<div><input id="t" placeholder="Title">'
        '<button id="add">Save</button></div><div id="list"></div>', """
        const kept = [];
        const list = document.getElementById('list');
        const draw = () => {
          list.innerHTML = '';
          kept.forEach((said, at) => {
            const row = document.createElement('div');
            row.className = 'row';
            row.textContent = said + ' ';
            const go = document.createElement('button');
            go.textContent = 'Remove';
            go.addEventListener('click',
                () => { kept.splice(at + 1, 1); draw(); });
            row.appendChild(go);
            list.appendChild(row);
          });
        };
        document.getElementById('add').addEventListener('click', () => {
          kept.push(document.getElementById('t').value || 'untitled');
          document.getElementById('t').value = '';
          draw();
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("not the one you pressed" in r.detail
               for r in run.failing), run.render()


def test_a_list_that_removes_the_right_row_is_left_alone(
        tmp_path: Path) -> None:
    """The twin. The same page, splicing where it was told to."""
    folder = build(
        tmp_path,
        '<div><input id="t" placeholder="Title">'
        '<button id="add">Save</button></div><div id="list"></div>', """
        const kept = [];
        const list = document.getElementById('list');
        const draw = () => {
          list.innerHTML = '';
          kept.forEach((said, at) => {
            const row = document.createElement('div');
            row.className = 'row';
            row.textContent = said + ' ';
            const go = document.createElement('button');
            go.textContent = 'Remove';
            go.addEventListener('click',
                () => { kept.splice(at, 1); draw(); });
            row.appendChild(go);
            list.appendChild(row);
          });
        };
        document.getElementById('add').addEventListener('click', () => {
          kept.push(document.getElementById('t').value || 'untitled');
          document.getElementById('t').value = '';
          draw();
        });
    """)

    run = check(folder)

    assert run.works, run.render()


def test_the_plan_reaches_what_only_exists_once_there_is_data(
        tmp_path: Path) -> None:
    """A to-do list at load is a box and a button.

    The checkbox and the Delete beside each row do not exist until a row
    does, so a plan derived from the page as it arrives cannot reach the
    things most likely to be wrong.
    """
    folder = build(
        tmp_path,
        '<div><input id="t" placeholder="Task">'
        '<button id="add">Add</button></div><ul id="list"></ul>', """
        document.getElementById('add').addEventListener('click', () => {
          const row = document.createElement('li');
          row.textContent = document.getElementById('t').value || 'untitled';
          const go = document.createElement('button');
          go.textContent = 'Delete';
          go.addEventListener('click', () => row.remove());
          row.appendChild(go);
          document.getElementById('list').appendChild(row);
          document.getElementById('t').value = '';
        });
    """)

    run = check(folder)

    assert run.works, run.render()
    assert any("with two saved" in c.what for c in run.plan), run.render()
    assert any("Delete" in c.what for c in run.plan), run.render()


def test_a_total_that_follows_the_list_up_and_not_down(
        tmp_path: Path) -> None:
    """An expense tracker that forgets to re-total when a row is deleted.

    Adding moves the total every time, so the page has said plainly that the
    total is about the list. Removing a row leaves it standing at a figure
    that is no longer owed. Nothing here does the arithmetic, and it does
    not need to.
    """
    folder = build(
        tmp_path,
        '<div><input id="d" placeholder="Description">'
        '<button id="add">Add</button></div>'
        '<p>Total: <span id="sum">0</span></p><ul id="list"></ul>', """
        let total = 0;
        const draw = () => document.getElementById('sum').textContent = total;
        document.getElementById('add').addEventListener('click', () => {
          const said = document.getElementById('d').value || 'something';
          const row = document.createElement('li');
          row.textContent = said + ' ';
          const go = document.createElement('button');
          go.textContent = 'Delete';
          go.addEventListener('click', () => { total -= 1; row.remove(); });
          row.appendChild(go);
          document.getElementById('list').appendChild(row);
          total += 1;
          draw();
          document.getElementById('d').value = '';
        });
    """)

    run = check(folder)

    assert not run.works, run.render()
    assert any("stopped following it" in r.detail
               for r in run.failing), run.render()


def test_a_total_that_follows_the_list_both_ways_is_left_alone(
        tmp_path: Path) -> None:
    """The twin. The same page, re-totalling on the way down."""
    folder = build(
        tmp_path,
        '<div><input id="d" placeholder="Description">'
        '<button id="add">Add</button></div>'
        '<p>Total: <span id="sum">0</span></p><ul id="list"></ul>', """
        let total = 0;
        const draw = () => document.getElementById('sum').textContent = total;
        document.getElementById('add').addEventListener('click', () => {
          const said = document.getElementById('d').value || 'something';
          const row = document.createElement('li');
          row.textContent = said + ' ';
          const go = document.createElement('button');
          go.textContent = 'Delete';
          go.addEventListener('click',
              () => { total -= 1; row.remove(); draw(); });
          row.appendChild(go);
          document.getElementById('list').appendChild(row);
          total += 1;
          draw();
          document.getElementById('d').value = '';
        });
    """)

    run = check(folder)

    assert run.works, run.render()

def test_a_converter_filling_the_other_box_is_left_alone(
        tmp_path: Path) -> None:
    """The twin, and the case this rule is narrowed around.

    Typing into celsius and finding the answer in fahrenheit is the program
    working. The box that was typed into still holds what was typed, which
    is the whole of the test.
    """
    folder = build(
        tmp_path,
        '<div><input id="c" placeholder="celsius">'
        '<input id="f" placeholder="fahrenheit">'
        '<button id="go">Convert</button></div><p id="out">ready</p>', """
        document.getElementById('go').addEventListener('click', () => {
          const c = document.getElementById('c').value;
          document.getElementById('f').value =
              c === '' ? '' : String(Number(c) * 9 / 5 + 32);
          document.getElementById('out').textContent = 'converted';
        });
    """)

    run = check(folder)

    assert run.works, run.render()
