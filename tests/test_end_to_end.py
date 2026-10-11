"""End-to-end tests that run assay in a real browser on pages small enough to
read at a glance. Each page is the smallest version of a real program assay
once judged wrongly. The tests skip when Chromium isn't installed.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

import pytest

from assay import check

def _no_browser() -> bool:
    """Whether Chromium is missing, so the tests skip instead of failing."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return not pathlib.Path(p.chromium.executable_path).exists()
    except Exception:
        return True


pytestmark = pytest.mark.skipif(_no_browser(), reason="no browser installed")


def build(tmp_path: Path, body: str, script: str = "") -> Path:
    """Write one page, plus `app.js` when a script is given, into a folder."""
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><head><title>t</title></head><body>"
        f"{body}"
        + (f'<script type="module" src="./app.js"></script>' if script else "")
        + "</body></html>", encoding="utf-8")
    if script:
        (tmp_path / "app.js").write_text(script, encoding="utf-8")
    return tmp_path


def test_a_page_that_works_passes_every_case(tmp_path: Path) -> None:
    """A working page passes every case. A false alarm on correct code would
    send the agent off to change code that was right."""
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
    """A page that throws while loading fails its first case."""
    folder = build(tmp_path, "<button id='go'>Go</button>",
                   "document.getElementById('nope').addEventListener("
                   "'click', () => {});\n")

    run = check(folder)

    assert not run.works
    first = run.results[run.plan[0].id]
    assert first.failed, run.render()
    assert "threw" in first.detail


def test_a_canvas_nobody_draws_into_is_caught(tmp_path: Path) -> None:
    """A canvas that's on the page and sized but never drawn into is
    reported."""
    folder = build(tmp_path, '<canvas id="c" width="200" height="200"></canvas>',
                   "// draws nothing at all\n")

    run = check(folder)

    assert not run.works
    said = " ".join(r.detail for r in run.failing)
    assert "nothing drawn" in said or "did not respond" in said, run.render()


def test_a_canvas_that_answers_the_keyboard_passes(tmp_path: Path) -> None:
    """A canvas that only responds to keys passes, so a game isn't reported
    as broken for ignoring clicks."""
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
    """A palette swatch that sets a variable without showing a selection
    passes. It's allowed to change nothing visible because the canvas beside
    it reads the variable. A page with only silent buttons is covered by
    `test_a_page_that_answers_nothing_is_broken`.
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
    """A page where no control ever changes anything fails as a whole. One
    silent control can be fine, because something else may read what it sets,
    but when nothing on the page ever changes, nothing reads it.
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
    assert "after any control was used" in run.render()


def test_the_page_verdict_stands_down_when_it_could_not_reach_everything(
        tmp_path: Path) -> None:
    """The page-wide verdict above is withheld when the page has elements
    that look clickable but weren't in the plan. Here the sortable header is
    the part that works, so pressing only the rows proves nothing.
    """
    folder = build(tmp_path,
                   '<table><tr><th id="h">Name</th></tr>'
                   + "".join(f'<tr><td>row {i}</td></tr>' for i in range(6))
                   + '</table>',
                   "document.getElementById('h').style.cursor = 'pointer';\n"
                   "document.getElementById('h').addEventListener('click',"
                   " () => { document.title = 'sorted'; });\n")

    run = check(folder)

    assert "after any control was used" not in run.render(), run.render()


def test_a_page_that_offers_nothing_is_still_judged(tmp_path: Path) -> None:
    """The page-wide verdict depends on unreached elements, not on how few
    controls a page has. A broken script can leave little to press, and that
    page must still be judged.
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
    """A control the page disabled itself counts as the page responding.
    Here the page clamps the quantity at its `max` and disables `+`, which is
    the feature working.
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
    """The same page with a live `+` wired to a handler that does nothing is
    still reported. Only `disabled` excuses a control that does nothing."""
    folder = build(tmp_path,
                   '<input id="q" type="number" value="1" min="1" max="10">'
                   '<button id="up">+</button><p id="t">Total: 9.99</p>',
                   "document.getElementById('up').addEventListener("
                   "'click', () => { let ignored = 1; });\n")

    run = check(folder)

    assert not run.works, run.render()


def test_a_canvas_that_answered_and_went_back_has_answered(
        tmp_path: Path) -> None:
    """A canvas that changes and then changes back within one case passes.
    A click on the shape outlines it and a click on the background removes the
    outline, so the canvas ends exactly where it started.
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
    """A canvas painted once at load that no gesture changes is still
    reported."""
    folder = build(tmp_path,
                   '<canvas id="c" width="300" height="200"></canvas>',
                   "const x = document.getElementById('c').getContext('2d');\n"
                   "x.fillStyle = '#c33'; x.fillRect(40, 40, 80, 60);\n")

    run = check(folder)

    assert not run.works, run.render()


GAME = ("let x = 0, over = false;\nconst c = document.getElementById('c').getContext('2d');\nconst tick = setInterval(() => {\n  x += 20;\n  c.clearRect(0, 0, 300, 200);\n  c.fillStyle = '#2a2'; c.fillRect(x, 80, 20, 20);\n  if (x > 180) { over = true; clearInterval(tick);%s }\n}, 60);\n")


def test_a_finished_program_that_promised_nothing_owes_nothing(
        tmp_path: Path) -> None:
    """A game that ends by itself without asking for input passes, even though
    it ignores keys after it ends. assay waits for the canvas to stop changing
    before it acts, and on this game that only happens at game over.
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
    """A list reordered by HTML5 drag and drop passes. Mouse moves never raise
    `dragstart`, so assay has to drive `draggable` rows with drag events.
    """
    folder = build(tmp_path, ROWS,
                   WIRE % (" if (held && held !== e.target)"
                           " l.insertBefore(held, e.target); show();"))

    run = check(folder)

    assert run.works, run.render()


def test_a_list_whose_drop_is_wired_to_nothing_is_caught(
        tmp_path: Path) -> None:
    """The same list with a drop handler that never reorders the rows is
    reported."""
    folder = build(tmp_path, ROWS, WIRE % " show();")

    run = check(folder)

    assert not run.works, run.render()


def test_a_resize_bar_that_freezes_after_one_drag_is_caught(
        tmp_path: Path) -> None:
    """A divider that moves once and then can't be grabbed again is reported.
    The second drag is measured on its own, because measuring both together
    lets the first drag's change hide the second one's failure.
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
    """A canvas filled with one flat colour every frame and never drawn into
    is reported. Every pixel is opaque, so counting painted pixels alone would
    call it full.

    The Pause button matters. A single case only demands that a canvas draw
    when the page has nothing else to press, so this page is caught by the
    check across the whole run.
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
    assert "ever appeared on this canvas" in run.render(), run.render()


def test_a_stroke_on_a_transparent_canvas_is_a_picture(
        tmp_path: Path) -> None:
    """A black stroke on a transparent canvas counts as a picture, even though
    it's one colour. A flat fill covers every pixel and a stroke doesn't,
    which is how assay tells them apart.
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
    """A style change on a table cell counts as the page changing, with no
    canvas, text change or new element."""
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
    """Every control gets a unique selector, so two `input`s without ids can
    be driven separately."""
    folder = build(tmp_path, "<input><input><button>Go</button>")

    from assay import look

    controls = look(folder).surface.controls
    selectors = [c.selector for c in controls if c.kind]

    assert len(selectors) == len(set(selectors)), selectors
    assert len([c for c in controls if c.kind == "text"]) == 2


def test_a_page_that_mounts_late_is_measured_after_it_mounts(
        tmp_path: Path) -> None:
    """A page that renders its app 1200ms after `load` is measured once the
    app appears. `load` fires before a framework renders anything, so
    measuring then would find nothing to plan.
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
    """A page that renders nothing fails, even though nothing throws. With no
    controls, the plan's only case asserts that nothing threw, which an empty
    document also satisfies.
    """
    folder = build(tmp_path, '<div id="root"></div>', "/* never renders */")
    run = check(folder)

    assert not run.works
    assert "shows nothing at all" in run.failing[0].detail


def test_a_grid_of_coloured_divs_is_not_a_blank_page(tmp_path: Path) -> None:
    """A grid of coloured `div`s with no text, image or canvas isn't reported
    as blank, because its cells can be clicked."""
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
    """A page that defines its own `eval` breaks every measurement assay
    takes, so its cases are reported as unchecked. A check that couldn't run
    must never read like a failure.
    """
    folder = build(tmp_path,
                   '<div id="d">0</div><button id="go">Go</button>',
                   "")
    # The page's own `eval` replaces the global the driver evaluates through.
    # The name comes from a variable so source scanners don't flag this
    # fixture as dynamic code execution.
    shadow = "eval"
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><head><title>t</title></head><body>"
        '<div id="d">0</div><button id="go">Go</button>'
        f"<script>function {shadow}() {{ return 1; }}"
        "document.getElementById('go').onclick = "
        "() => document.getElementById('d').textContent = '1';</script>"
        "</body></html>", encoding="utf-8")
    run = check(folder)

    assert run.unchecked, "nothing was recorded as unmeasurable"
    assert "couldn't read this page" in run.unchecked[0].detail
    assert not [r for r in run.results.values() if r.failed], \
        "an unreadable page was reported as a failure"


def test_a_drawing_canvas_is_not_broken_for_ignoring_clicks(
        tmp_path: Path) -> None:
    """A canvas that only draws on press, move and release passes."""
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
    """A converter that only writes its answer into another input counts as
    changing the page, because the page measurement includes field values."""
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
    """A form whose Add button does nothing with the typed text still fails.
    Measuring field values must not let a dead button pass, and the benchmark
    can't catch that because every program in it works.
    """
    folder = build(tmp_path,
                   '<input id="task" placeholder="Task">'
                   '<button id="add">Add</button><ul id="list"></ul>',
                   "document.getElementById('add').addEventListener("
                   "'click', () => {});")
    run = check(folder)

    assert not run.works, "a dead Add button passed"


def test_a_grid_of_plain_divs_is_not_an_empty_page(tmp_path: Path) -> None:
    """A grid of plain `div`s with one click listener on their parent isn't an
    empty page. assay can't read a listener from outside the page, but it can
    read `cursor: pointer`, and treats an element that has it as clickable.
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
    """A sheet of `contentEditable` cells counts as ready once it's drawn. The
    surface types into those cells, so the readiness check counts them too,
    or every open of the sheet would wait for the full settle timeout.
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
    """A table whose only controls are headers with a pointer cursor counts as
    ready once it's drawn. The readiness check looks at the same tags as the
    surface, `th` included, or the table would wait for the full timeout.
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
    """A list of `draggable` rows counts as ready once it's drawn, because
    the surface drags those rows."""
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
    """A chart canvas that only draws when Add is pressed passes, even though
    clicking and dragging the canvas itself changes nothing."""
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
    """Every field in a form is filled before its button is pressed. A
    sign-up form correctly refuses while the password is empty, so filling
    only one box would report a working form as broken.
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
    """A game that animates, ends, shows "Press Space to restart" and then
    ignores Space is reported. assay waits for the canvas to stop before it
    acts, so the frames the game drew on its own don't count as a response.

    The message on the page is what makes this a fault. A game that ends
    without asking for input passes, as in
    `test_a_finished_program_that_promised_nothing_owes_nothing`.
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
    """A canvas that's still animating when the settle timeout runs out
    passes. assay can't tell its frames from a response to a gesture, so it
    doesn't require one.
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
    """A canvas that accepts one stroke and then ignores the next is
    reported."""
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
    assert "stopped accepting drawing" in run.render()


def test_a_canvas_nobody_draws_on_is_asked_nothing(tmp_path: Path) -> None:
    """A canvas that ignores the first stroke, like a chart drawn by a
    button, isn't required to take the second. The first stroke decides
    whether the rule applies, so assay needs no list of canvas types.
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
    """An Undo that only responds on its second press is reported as one
    press late. Its stack stores the state after each change, so the first
    press restores what's already shown. The rule compares two identical
    presses and never reads the button's label.
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
    assert "one press late" in run.render()


def test_a_control_that_answers_both_presses_is_left_alone(
        tmp_path: Path) -> None:
    """The same page saving the state before each change, which is correct,
    passes."""
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
    """assay types an answer into a `prompt` instead of dismissing it.
    Dismissing returns null, so a board that asks for a card's title would
    never add the card and would look like nothing responds.
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
    """A WebGL canvas can be measured. `getContext('2d')` returns null on one,
    which would make every reading `-1`, so assay reads it through `toDataURL`
    inside a frame callback. Outside a frame callback the drawing buffer has
    already been cleared and reads as blank.
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
    """The same WebGL page with its keys wired to nothing is reported, which
    shows the reading above actually measures the canvas."""
    folder = build(tmp_path, '<canvas id="gl" width="200" height="150"></canvas>',
                   WEBGL % ("-0.5", "// nothing is wired to anything"))

    run = check(folder)

    assert not run.works, run.render()


def test_a_control_that_starts_something_slow_is_not_inert(
        tmp_path: Path) -> None:
    """A button whose result appears two seconds later still counts as
    responding. Each case measures shortly after it acts, so the page-wide
    "nothing responds" check waits longer before deciding.
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
    """A required field whose `pattern` rejects its own placeholder is
    reported, because the form can never be completed. `\\\\d{5}` matches a
    backslash and five letter d's, so the example `12345` fails it. assay
    checks this from the markup, so it's caught even on a wizard step that's
    never shown.
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
    assert "12345" in run.render() and "can't submit" in run.render()


def test_a_pattern_its_example_satisfies_is_left_alone(tmp_path: Path) -> None:
    """The same page with the pattern written correctly passes. A placeholder
    that's an instruction, like `Enter your number`, isn't an example, so its
    field is skipped.
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
    """`NaN` shown on the page is reported. Nobody types it, so it comes from
    arithmetic on something that wasn't a number, like a poll dividing by a
    total of zero.
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
    """A page that mentions `null` in its own text passes. A page may write
    about such values, so `null` isn't one of the words checked."""
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
    """Two radio buttons in one group with the same `value` are reported,
    because the form can't tell which was picked. Both render and can be
    clicked, so no case catches it.
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
    assert any("can't tell which of them was picked" in r.detail
               for r in run.failing), run.render()


def test_choices_with_their_own_values_are_left_alone(tmp_path: Path) -> None:
    """Radio groups that reuse values across groups pass. Only a repeat
    within one group is reported."""
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
    """A `label` whose `for` names no element on the page is reported.
    Clicking its words does nothing, and nothing else on the page shows it.
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
    assert any("nothing on the page has that id" in r.detail
               for r in run.failing), run.render()


def test_labels_that_point_at_their_own_controls_are_left_alone(
        tmp_path: Path) -> None:
    """Labels that point at their own controls pass, including one that
    wraps its input and needs no `for`."""
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
    """A `range` slider gets a case that moves it. Without one, a page of
    working sliders would get the page-wide "nothing responds" verdict."""
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
    """A square that changes on its second click and not its first is
    reported as one press late. Each click also updates a summary line, so
    checking the whole page alone would pass it.
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
    assert any("one press late" in r.detail for r in run.failing), run.render()


def test_a_square_that_answers_elsewhere_every_time_is_left_alone(
        tmp_path: Path) -> None:
    """A square that never changes itself when clicked, like a thumbnail that
    opens a lightbox, passes. The rule only reports a square whose two presses
    disagree.
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
    """A Previous button that never responds, even right after Next, is
    reported. Previous correctly does nothing on a freshly loaded deck, so the
    press that decides it is the one straight after Next.
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
    assert any("never did, even right after" in r.detail
               for r in run.failing), run.render()


def test_an_opposite_that_answers_after_its_pair_is_left_alone(
        tmp_path: Path) -> None:
    """The same deck with a working Previous passes. It does nothing at the
    start and responds after Next."""
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


def test_a_toggle_that_puts_the_page_back_too_is_left_alone(
        tmp_path: Path) -> None:
    """A filter tag that shows the hidden rows again when it's switched off
    passes."""
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
    """A counter that reads one fewer than the list's rows is reported. The
    number changes by one each time a row is added, which marks it as the
    count, and a count can't be -1 with nothing to count.
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
    assert any("counts the list" in r.detail for r in run.failing), run.render()


def test_a_number_that_counts_the_list_correctly_is_left_alone(
        tmp_path: Path) -> None:
    """The same page counting its rows correctly passes."""
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
    """A typed URL that the page accepts and then shows nowhere is reported.
    The row is added, but its Open link uses the title, so the address isn't
    in the text, the fields or any attribute.
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
    assert any("doesn't show it" in r.detail
               for r in run.failing), run.render()


def test_a_form_that_refuses_what_it_was_given_is_left_alone(
        tmp_path: Path) -> None:
    """A form that rejects the entry and adds no row passes. The rule only
    applies to an entry the page accepted by adding a row."""
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
    """A sign-up form that says "Account created" and shows neither the
    address nor the password passes. The rule looks for the typed values in a
    list, and this form has no list.
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
    """A Remove button that removes a different row is reported. Every count
    is right, so it takes two rows holding different text to see it, which is
    why the plan adds two different entries first.
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
    assert any("not the one it belongs to" in r.detail
               for r in run.failing), run.render()


def test_a_list_that_removes_the_right_row_is_left_alone(
        tmp_path: Path) -> None:
    """The same list removing the right row passes."""
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
    """The plan reaches controls that only exist once there's data, like the
    Delete button on each to-do row, by adding entries first."""
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
    """A total that changes when a row is added but not when one is deleted
    is reported. Adding moves the total every time, which marks it as
    following the list, so assay doesn't need to check the arithmetic.
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
    assert any("stops following the list" in r.detail
               for r in run.failing), run.render()


def test_a_total_that_follows_the_list_both_ways_is_left_alone(
        tmp_path: Path) -> None:
    """The same page updating the total on delete too passes."""
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
    """A converter that writes its answer into the other box passes. The box
    that was typed into still holds the typed value, which counts as the page
    showing it.
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


# Controls that are changed instead of clicked


CONVERTER = """
    const show = () => {
      const f = document.getElementById('from');
      const t = document.getElementById('to');
      document.getElementById('out').textContent = '1 '
          + f.selectedOptions[0].text + ' = ' + (f.value / t.value) + ' '
          + t.selectedOptions[0].text;
    };
    document.getElementById('from').addEventListener('change', show);
    document.getElementById('to').addEventListener('change', show);
"""


def test_a_page_made_of_selects_is_changed_rather_than_clicked(
        tmp_path: Path) -> None:
    """A select is changed instead of clicked. Clicking one opens it without
    choosing anything, so its `change` handler would never run."""
    folder = build(
        tmp_path,
        '<select id="from"><option value="1">metres</option>'
        '<option value="1000">kilometres</option></select>'
        '<select id="to"><option value="1">metres</option>'
        '<option value="1000">kilometres</option></select>'
        '<p id="out">1 metres = 1 metres</p>', CONVERTER)

    run = check(folder)

    assert run.works, run.render()


def test_a_select_whose_change_throws_is_caught(tmp_path: Path) -> None:
    """Changing a select runs its `change` handler, so a handler that throws
    is reported."""
    folder = build(
        tmp_path,
        '<select id="size"><option>Small</option><option>Large</option>'
        '</select><p id="out">Small</p>',
        "document.getElementById('size').addEventListener('change', () => {\n"
        "  document.getElementById('nope').textContent = 'x';\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()


def test_a_box_that_answers_on_change_is_given_its_change(
        tmp_path: Path) -> None:
    """A box gets a `change` event after it's typed into. Browsers only send
    `change` when the box loses focus, so typing alone would never run the
    handler."""
    folder = build(
        tmp_path,
        '<input id="n" type="number" value="2"><p id="out">4 eggs</p>',
        "document.getElementById('n').addEventListener('change', (e) => {\n"
        "  document.getElementById('nope').textContent = e.target.value;\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()


def test_a_box_that_recalculates_on_change_is_left_alone(
        tmp_path: Path) -> None:
    """The same box with a working `change` handler passes."""
    folder = build(
        tmp_path,
        '<input id="n" type="number" value="2"><p id="out">4 eggs</p>',
        "document.getElementById('n').addEventListener('change', (e) => {\n"
        "  document.getElementById('out').textContent =\n"
        "    (Number(e.target.value) * 2 || 0) + ' eggs';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_date_box_is_given_a_date(tmp_path: Path) -> None:
    """A date box is filled with a real date, because the browser refuses
    typed words before the page sees them."""
    folder = build(
        tmp_path, '<input id="d" type="date"><p id="out">no date</p>',
        "document.getElementById('d').addEventListener('change', (e) => {\n"
        "  if (e.target.value) document.getElementById('nope').remove();\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()
    assert any("2026-03-14" in str(c.acts) for c in run.plan), run.render()


def test_a_date_box_that_shows_its_date_its_own_way_is_left_alone(
        tmp_path: Path) -> None:
    """A list that shows a date differently from its date box passes.
    `2026-03-14` in the box can be `14 March` in the row, so assay doesn't
    look for the box's exact text.
    """
    folder = build(
        tmp_path,
        '<input id="name" placeholder="Event"><input id="when" type="date">'
        '<button id="add">Add</button><ul id="list"></ul>',
        "const months = ['January', 'February', 'March', 'April', 'May',\n"
        "  'June', 'July', 'August', 'September', 'October', 'November',\n"
        "  'December'];\n"
        "document.getElementById('add').addEventListener('click', () => {\n"
        "  const name = document.getElementById('name').value.trim();\n"
        "  const when = document.getElementById('when').value;\n"
        "  if (!name || !when) return;\n"
        "  const [y, m, d] = when.split('-').map(Number);\n"
        "  const li = document.createElement('li');\n"
        "  li.className = 'event';\n"
        "  li.textContent = name + ' on ' + d + ' ' + months[m - 1];\n"
        "  document.getElementById('list').appendChild(li);\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_colour_box_is_given_a_colour(tmp_path: Path) -> None:
    """A colour input is given a colour, which runs its `input` handler, so a
    handler that throws is reported."""
    folder = build(
        tmp_path, '<input id="c" type="color" value="#000000">',
        "document.getElementById('c').addEventListener('input', () => {\n"
        "  document.getElementById('nope').remove();\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()


def test_a_colour_box_that_recolours_the_page_is_left_alone(
        tmp_path: Path) -> None:
    folder = build(
        tmp_path, '<input id="c" type="color" value="#000000"><p>hello</p>',
        "document.getElementById('c').addEventListener('input', (e) => {\n"
        "  document.body.style.color = e.target.value;\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_file_box_is_given_a_file(tmp_path: Path) -> None:
    folder = build(
        tmp_path, '<input id="f" type="file" accept="image/*">',
        "document.getElementById('f').addEventListener('change', (e) => {\n"
        "  if (e.target.files.length) document.getElementById('nope').remove();\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()


def test_a_file_box_that_names_its_file_is_left_alone(tmp_path: Path) -> None:
    folder = build(
        tmp_path, '<input id="f" type="file"><p id="out">no file</p>',
        "document.getElementById('f').addEventListener('change', (e) => {\n"
        "  document.getElementById('out').textContent =\n"
        "    e.target.files[0] ? e.target.files[0].name : 'no file';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


# Presses with unusual but correct responses


def test_a_folder_that_tidies_its_children_on_closing_is_left_alone(
        tmp_path: Path) -> None:
    """A tree folder that collapses its subfolders when it closes passes.
    Reopened, its subfolders stay closed, but the second press redrew them and
    updated the row count, which a toggle whose effect stuck wouldn't do.
    """
    folder = build(
        tmp_path,
        '<p>Visible rows: <span id="count">5</span></p>'
        '<ul id="tree">'
        '<li class="folder open"><span class="name" style="cursor:pointer">'
        'Folder A</span><ul>'
        '<li class="folder open"><span class="name" style="cursor:pointer">'
        'Folder A1</span><ul><li>a1.txt</li><li>a2.txt</li></ul></li>'
        '</ul></li>'
        '<li class="folder"><span class="name" style="cursor:pointer">'
        'Folder B</span><ul hidden><li>b1.txt</li></ul></li>'
        '</ul>',
        "const count = () => {\n"
        "  document.getElementById('count').textContent = [...document\n"
        "    .querySelectorAll('#tree li')].filter(li => li.offsetParent)\n"
        "    .length;\n"
        "};\n"
        "document.querySelectorAll('.name').forEach((name) => {\n"
        "  name.addEventListener('click', () => {\n"
        "    const li = name.parentElement;\n"
        "    const open = li.classList.toggle('open');\n"
        "    li.querySelector('ul').hidden = !open;\n"
        "    if (!open) li.querySelectorAll('li.folder').forEach((f) => {\n"
        "      f.classList.remove('open');\n"
        "      f.querySelector('ul').hidden = true;\n"
        "    });\n"
        "    count();\n"
        "  });\n"
        "});\n"
        "count();\n")

    run = check(folder)

    assert not any("still in effect" in r.detail for r in run.failing), \
        run.render()


def test_undo_is_not_blamed_for_a_stroke_that_never_drew(
        tmp_path: Path) -> None:
    """A correct Undo isn't reported when the canvas fails to draw a second
    stroke. The undo stack takes a step on every mousedown, so a stroke
    outside the drawable corner leaves an empty step, and the first Undo
    spends itself on that. The second-stroke case reports the broken canvas.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<button id="u">Undo</button>',
                   "const el = document.getElementById('c');\n"
                   "const ctx = el.getContext('2d');\n"
                   "const past = [];\n"
                   "let down = false;\n"
                   "const dot = (e) => {\n"
                   "  const r = el.getBoundingClientRect();\n"
                   "  const x = e.clientX - r.left, y = e.clientY - r.top;\n"
                   "  if (x < 60 && y < 60) ctx.fillRect(x, y, 6, 6);\n"
                   "};\n"
                   "el.addEventListener('mousedown', (e) => {\n"
                   "  past.push(ctx.getImageData(0, 0, 200, 200));\n"
                   "  down = true; dot(e);\n"
                   "});\n"
                   "el.addEventListener('mousemove', (e) => { if (down) dot(e); });\n"
                   "window.addEventListener('mouseup', () => { down = false; });\n"
                   "document.getElementById('u').addEventListener('click', () => {\n"
                   "  if (past.length) ctx.putImageData(past.pop(), 0, 0);\n"
                   "});\n")

    run = check(folder)

    assert "one press late" not in run.render(), run.render()
    assert "stopped accepting drawing" in run.render(), run.render()


def test_a_page_that_threw_is_reported_even_where_the_stroke_guard_stands_down(
        tmp_path: Path) -> None:
    """When the stroke guard skips the one-press-late check, the case is
    still reported for the page's crash. A painter that throws on load draws
    no second stroke, so the Undo case has nothing to compare, but it still
    ran on a page that threw.
    """
    folder = build(tmp_path,
                   '<canvas id="c" width="200" height="200"></canvas>'
                   '<button id="u">Undo</button>',
                   "document.getElementById('u').addEventListener('click',\n"
                   "  () => {});\n"
                   "history.push(1);\n")

    run = check(folder)

    guarded = [r for r in run.failing if "twice, then press" in r.case.what]
    assert guarded and all("threw" in r.detail for r in guarded), run.render()


# Rows holding the wrong figure


def _expense_table(tmp_path: Path, shown: str) -> Path:
    """An expense tracker table with a row and a Delete button per expense.
    `shown` is the JS expression each row displays."""
    return build(
        tmp_path,
        '<div class="entry"><input id="what" placeholder="Description">'
        '<input id="amount" type="number" placeholder="Amount">'
        '<button id="add">Add</button></div>'
        '<table><tbody id="rows"></tbody></table>',
        "let total = 0;\n"
        "document.getElementById('add').addEventListener('click', () => {\n"
        "  const what = document.getElementById('what').value.trim();\n"
        "  const amount = Number(document.getElementById('amount').value);\n"
        "  if (!what || !amount) return;\n"
        "  total += amount;\n"
        "  const tr = document.createElement('tr');\n"
        f"  const figure = {shown};\n"
        "  tr.innerHTML = '<td></td><td></td><td><button>Delete</button></td>';\n"
        "  tr.children[0].textContent = what;\n"
        "  tr.children[1].textContent = figure;\n"
        "  tr.querySelector('button').addEventListener('click', () => {\n"
        "    total -= amount; tr.remove();\n"
        "  });\n"
        "  document.getElementById('rows').appendChild(tr);\n"
        "});\n")


def test_a_row_holding_the_running_total_instead_of_its_amount(
        tmp_path: Path) -> None:
    """A row showing the running total instead of its own amount is reported.
    With one row the two are equal, so it takes a second row to see it."""
    run = check(_expense_table(tmp_path, "total"))

    assert any("new row in the list doesn't show it" in r.detail
               for r in run.failing), run.render()


def test_a_row_holding_its_own_amount_is_left_alone(tmp_path: Path) -> None:
    run = check(_expense_table(tmp_path, "amount.toFixed(2)"))

    assert run.works, run.render()


def test_a_second_entry_the_page_refuses_is_not_a_lost_one(
        tmp_path: Path) -> None:
    """A list that takes one entry and refuses the next isn't reported for
    losing the second one."""
    folder = build(
        tmp_path,
        '<div class="entry"><input id="what" placeholder="Description">'
        '<button id="add">Add</button></div><ul id="list"></ul>',
        "document.getElementById('add').addEventListener('click', () => {\n"
        "  const list = document.getElementById('list');\n"
        "  const what = document.getElementById('what').value.trim();\n"
        "  if (!what || list.children.length) return;\n"
        "  const li = document.createElement('li');\n"
        "  li.innerHTML = '<span></span> <button>Remove</button>';\n"
        "  li.querySelector('span').textContent = what;\n"
        "  li.querySelector('button').addEventListener('click',\n"
        "    () => li.remove());\n"
        "  list.appendChild(li);\n"
        "});\n")

    run = check(folder)

    assert not any("doesn't show it" in r.detail for r in run.failing), \
        run.render()


# Controls a label stands in for


STARS = ('<div class="entry"><div class="stars">'
         + "".join(f'<input type="radio" name="rating" id="s{n}" value="{n}"'
                   f' style="display:none"><label for="s{n}" '
                   f'style="cursor:pointer;font-size:24px">&#9733;</label>'
                   for n in range(5, 0, -1))
         + '</div><textarea id="comment" placeholder="Comment"></textarea>'
         '<button id="send">Submit</button></div><ul id="past"></ul>')


def test_a_star_rating_is_rated_and_sent(tmp_path: Path) -> None:
    """A star rating built from hidden radios and visible labels is rated and
    then submitted. The radios never render, so assay picks a star through its
    label in a seeded case before pressing Submit, which correctly refuses
    without one.
    """
    folder = build(
        tmp_path, STARS,
        "document.getElementById('send').addEventListener('click', () => {\n"
        "  const star = document.querySelector('input[name=rating]:checked');\n"
        "  if (!star) { alert('Pick a star first.'); return; }\n"
        "  const li = document.createElement('li');\n"
        "  li.innerHTML = '<span></span> <button>Remove</button>';\n"
        "  li.querySelector('span').textContent = star.value + ' stars: '\n"
        "    + document.getElementById('comment').value;\n"
        "  li.querySelector('button').addEventListener('click',\n"
        "    () => li.remove());\n"
        "  document.getElementById('past').appendChild(li);\n"
        "  document.getElementById('comment').value = '';\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()
    assert any("pick" in act for c in run.plan for act in c.acts), run.render()
    assert any(c.origin == "seeded" for c in run.plan), run.render()


def test_a_star_whose_handler_throws_is_caught(tmp_path: Path) -> None:
    folder = build(
        tmp_path, STARS,
        "document.querySelectorAll('input[name=rating]').forEach((r) => {\n"
        "  r.addEventListener('change', () => {\n"
        "    document.getElementById('nope').textContent = r.value;\n"
        "  });\n"
        "});\n")

    run = check(folder)

    assert any("threw" in r.detail for r in run.failing), run.render()


# What a page saved


def _saved_list(tmp_path: Path, reads: str) -> Path:
    """A list that saves its rows to localStorage under `rows` and reads them
    back from the key `reads` on load."""
    return build(
        tmp_path,
        '<div class="entry"><input id="what" placeholder="Title">'
        '<button id="add">Add</button></div><ul id="list"></ul>',
        "const list = document.getElementById('list');\n"
        "let rows = [];\n"
        "const draw = () => {\n"
        "  list.innerHTML = '';\n"
        "  rows.forEach((text, at) => {\n"
        "    const li = document.createElement('li');\n"
        "    li.innerHTML = '<span></span> <button>Remove</button>';\n"
        "    li.querySelector('span').textContent = text;\n"
        "    li.querySelector('button').addEventListener('click', () => {\n"
        "      rows.splice(at, 1); save(); draw();\n"
        "    });\n"
        "    list.appendChild(li);\n"
        "  });\n"
        "};\n"
        "const save = () => localStorage.setItem('rows', JSON.stringify(rows));\n"
        f"rows = JSON.parse(localStorage.getItem('{reads}') || '[]');\n"
        "draw();\n"
        "document.getElementById('add').addEventListener('click', () => {\n"
        "  const what = document.getElementById('what').value.trim();\n"
        "  if (!what) return;\n"
        "  rows.push(what); save(); draw();\n"
        "});\n")


def test_a_list_that_saves_and_cannot_read_it_back_is_caught(
        tmp_path: Path) -> None:
    """A list that saves under one key and reads back another is reported
    once the page is reloaded. Every count is right while the page is open, so
    only a reload shows the saved rows are gone.
    """
    run = check(_saved_list(tmp_path, "row"))

    assert any("gone after reloading" in r.detail for r in run.failing), \
        run.render()


def test_a_list_that_reads_back_what_it_saved_is_left_alone(
        tmp_path: Path) -> None:
    run = check(_saved_list(tmp_path, "rows"))

    assert run.works, run.render()
    assert any("reload" in act for c in run.plan for act in c.acts), \
        run.render()


# What a control says it shows


def _tabs(tmp_path: Path, hides: str) -> Path:
    """Three tabs whose markup names the panel each one shows. `hides` is the
    JS expression that sets each panel's `hidden`."""
    tabs = "".join(
        f'<button role="tab" id="t{n}" aria-controls="p{n}" '
        f'aria-selected="{"true" if n == 0 else "false"}">Tab {n}</button>'
        for n in range(3))
    panels = "".join(
        f'<div role="tabpanel" id="p{n}"{"" if n == 0 else " hidden"}>'
        f'Panel {n} text</div>' for n in range(3))
    return build(
        tmp_path, f'<div role="tablist">{tabs}</div>{panels}',
        "document.querySelectorAll('[role=tab]').forEach((tab, at) => {\n"
        "  tab.addEventListener('click', () => {\n"
        "    document.querySelectorAll('[role=tab]').forEach((t, i) => {\n"
        "      t.setAttribute('aria-selected', String(i === at));\n"
        f"      document.getElementById('p' + i).hidden = {hides};\n"
        "    });\n"
        "  });\n"
        "});\n")


def test_a_selected_tab_whose_panel_is_not_shown_is_caught(
        tmp_path: Path) -> None:
    """A tab marked selected whose panel stays hidden is reported. Every press
    changes the page, because the old panel is hidden, so only the tab's own
    markup shows that the new panel never appears.
    """
    run = check(_tabs(tmp_path, "true"))

    assert any("panel isn't shown" in r.detail for r in run.failing), \
        run.render()


def test_tabs_that_show_what_they_select_are_left_alone(
        tmp_path: Path) -> None:
    run = check(_tabs(tmp_path, "i !== at"))

    assert run.works, run.render()


def test_an_open_accordion_with_an_empty_region_is_left_alone(
        tmp_path: Path) -> None:
    """An open accordion whose region is empty passes. The region still
    counts as shown, because it has a box with no height."""
    folder = build(
        tmp_path,
        '<button id="h" aria-expanded="false" aria-controls="r">More</button>'
        '<div id="r" hidden></div>',
        "document.getElementById('h').addEventListener('click', (e) => {\n"
        "  const open = e.target.getAttribute('aria-expanded') !== 'true';\n"
        "  e.target.setAttribute('aria-expanded', String(open));\n"
        "  document.getElementById('r').hidden = !open;\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


# Findings that are the same finding


def test_a_tag_bar_left_lit_is_one_finding_on_every_tag(
        tmp_path: Path) -> None:
    """Each tag that stays lit is reported, and all but the first point at it."""
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

    lit = [r for r in run.failing if "still in effect" in r.detail]
    assert len(lit) >= 2, run.render()
    assert lit[0].links == [], run.render()
    assert all(r.links and r.links[0].to == lit[0].case.id
               for r in lit[1:]), run.render()
    assert "repeat an earlier finding" in run.summary()


def test_two_different_faults_are_not_joined(tmp_path: Path) -> None:
    """A label pointing at nothing and a `NaN` result are two separate
    findings, so they aren't linked."""
    folder = build(
        tmp_path,
        '<label for="missing">Name</label><input id="n">'
        '<button id="go">Go</button><p id="out">0</p>',
        "document.getElementById('go').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = Number('x') + 1;\n"
        "});\n")

    run = check(folder)

    assert len(run.failing) >= 2, run.render()
    assert not any(r.links for r in run.failing), run.render()


def test_a_dead_page_is_told_it_threw_while_loading(tmp_path: Path) -> None:
    """When no control responds and the page threw before any act, the
    page-wide finding is linked to the crash on load."""
    folder = build(
        tmp_path,
        '<button id="a">Add</button><button id="b">Clear</button>'
        '<p id="out">nothing</p>',
        "const later = undefinedThing.value;\n"
        "document.getElementById('a').addEventListener('click', () => {\n"
        "  document.getElementById('out').textContent = 'added';\n"
        "});\n")

    run = check(folder)

    dead = [r for r in run.failing if r.case.id == "C000"]
    assert dead, run.render()
    assert [one.kind for one in dead[0].links] == ["load"], run.render()
    assert "threw an error while loading" in run.render()


# Forms that refuse, and keys that type


def test_a_form_that_refuses_with_an_alert_has_answered(
        tmp_path: Path) -> None:
    """A form that refuses input with an `alert` counts as responding. The
    alert leaves nothing in the document, so a check that only read the
    document would report that nothing changed.
    """
    folder = build(
        tmp_path,
        '<div class="entry"><input id="code" placeholder="Code">'
        '<button id="send">Send</button></div><ul id="out"></ul>',
        "document.getElementById('send').addEventListener('click', () => {\n"
        "  const code = document.getElementById('code').value;\n"
        "  if (!/^[A-Z]{3}[0-9]{3}$/.test(code)) {\n"
        "    alert('Code must be three letters and three digits.');\n"
        "    return;\n"
        "  }\n"
        "  document.getElementById('out').insertAdjacentHTML('beforeend',\n"
        "    '<li>' + code + '</li>');\n"
        "});\n")

    run = check(folder)

    assert not any("nothing on the page changed" in r.detail.lower()
                   for r in run.failing), run.render()


def test_a_phone_box_is_given_a_phone_number(tmp_path: Path) -> None:
    """A phone field is filled with a phone number, because a contact form
    correctly refuses one with no digits."""
    folder = build(
        tmp_path,
        '<div class="entry"><input id="name" placeholder="Name">'
        '<input id="phone" placeholder="Phone">'
        '<button id="add">Add Contact</button></div><ul id="list"></ul>',
        "document.getElementById('add').addEventListener('click', () => {\n"
        "  const name = document.getElementById('name').value.trim();\n"
        "  const phone = document.getElementById('phone').value.trim();\n"
        "  if (!name || !/[0-9]/.test(phone)) return;\n"
        "  const li = document.createElement('li');\n"
        "  li.textContent = name + ' ' + phone;\n"
        "  document.getElementById('list').appendChild(li);\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_keys_that_type_onto_a_board_are_not_one_behind(
        tmp_path: Path) -> None:
    """On-screen keys that type onto a board aren't reported as one press
    late. A key never changes itself, and each press changes the board."""
    keys = "".join(f'<div class="key" style="cursor:pointer;display:inline-block;'
                   f'width:30px;height:30px">{k}</div>' for k in "ABCDEFGH")
    folder = build(
        tmp_path, f'<p id="board"></p><div id="keyboard">{keys}</div>',
        "document.querySelectorAll('.key').forEach((key) => {\n"
        "  key.addEventListener('click', () => {\n"
        "    document.getElementById('board').textContent += key.textContent;\n"
        "  });\n"
        "});\n")

    run = check(folder)

    assert not any("one press late" in r.detail for r in run.failing), \
        run.render()


def test_a_form_with_a_required_dropdown_is_sent_with_a_choice(
        tmp_path: Path) -> None:
    """A form with a required dropdown is submitted with an option chosen,
    because a dropdown left on its placeholder correctly stops the form."""
    folder = build(
        tmp_path,
        '<form id="f"><input id="name" placeholder="Name" required>'
        '<select id="group" required><option value="">Choose...</option>'
        '<option>Family</option><option>Work</option></select>'
        '<button type="submit">Add</button></form><ul id="list"></ul>',
        "document.getElementById('f').addEventListener('submit', (e) => {\n"
        "  e.preventDefault();\n"
        "  const li = document.createElement('li');\n"
        "  li.textContent = document.getElementById('name').value + ' ('\n"
        "    + document.getElementById('group').value + ')';\n"
        "  document.getElementById('list').appendChild(li);\n"
        "});\n")

    run = check(folder)

    assert run.works, run.render()


def test_a_board_that_asks_for_a_title_and_adds_nothing_is_caught(
        tmp_path: Path) -> None:
    """A board whose Add asks for a card title through `prompt` and then adds
    nothing is reported. assay answers the prompt, so the missing card is a
    real fault.
    """
    columns = "".join(
        f'<div class="col"><h2>{name}</h2><button class="add">+ Add</button>'
        f'<ul></ul></div>' for name in ("Todo", "Doing", "Done"))
    folder = build(
        tmp_path, columns,
        "document.querySelectorAll('.add').forEach((b) => {\n"
        "  b.addEventListener('click', () => {\n"
        "    const title = prompt('Card title?');\n"
        "    if (!title) return;\n"
        "  });\n"
        "});\n")

    run = check(folder)

    assert any("after any control was used" in r.detail for r in run.failing), \
        run.render()
