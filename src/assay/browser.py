"""Opening a page, measuring it, and doing things to it.

Everything here is a measurement. Nothing in this module decides whether a
program is good. It reports painted pixels, centroids, colours, text and
element counts, and `qa` decides. That split is deliberate: a measurement that
also judges is one you cannot check.

Most of what follows exists because a naive version of it returned a confident
wrong answer about a real program. Those cases are named where they apply.
None of them is hypothetical.
"""

from __future__ import annotations

import contextlib
import http.server
import re
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import (Any, Dict, Iterator, List, NamedTuple, Optional,
                    Sequence, Tuple)

#: Where on a canvas to click when nothing says otherwise. See
#: `surface.SAFE_LOW` for why it is this and not the centre.
CANVAS_X, CANVAS_Y = 0.22, 0.78


@dataclass
class Element:
    """One element as the browser actually laid it out."""

    tag: str
    selector: str
    width: int = 0
    height: int = 0
    visible: bool = True
    text: str = ""
    #: `button`, `text`, `checkbox`, `select`, `canvas`, `link`… Empty for
    #: anything that is not a control. A tag does not answer this: `<input>`
    #: is a textbox, a checkbox, a slider or a button depending on one
    #: attribute, and a plan that treats them alike types into a checkbox.
    kind: str = ""
    label: str = ""
    enabled: bool = True
    #: Whether the page refuses typing into it. A readonly box is an output.
    readonly: bool = False
    #: A handle carrying `draggable="true"`, which moves only through the
    #: HTML5 drag protocol and not through mouse events.
    grabbed: bool = False
    #: The form, or failing that the container, this control sits in. A field
    #: and a button are a pair when they share one.
    pairing: int = 0
    #: Which widget this belongs to: the smallest ancestor holding both a
    #: field and a button. A board with three columns has three, and pairing
    #: one column's field with another's button tests nothing.
    group: int = 0
    painted: Optional[int] = None
    loaded: Optional[bool] = None
    src: str = ""


# --------------------------------------------------------------------------
# Serving
# --------------------------------------------------------------------------

@contextlib.contextmanager
def serve(root: Path) -> Iterator[str]:
    """Serve a folder over http and yield its base URL.

    **A page is served, never opened off the disk.** A `file://` origin is
    opaque, so the browser refuses every `<script type="module">` before a line
    of it runs: the page renders, every element is present and correctly sized,
    and nothing works. The module never loads, so it cannot even raise the
    error that would give it away. Any page using modules measures as a
    different program when opened off disk.
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a: Any, **kw: Any) -> None:
            super().__init__(*a, directory=str(root), **kw)

        def log_message(self, *a: Any) -> None:
            return

    class Server(socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


# --------------------------------------------------------------------------
# Measuring
# --------------------------------------------------------------------------

#: Every control the page renders, each with a selector naming exactly one
#: element. Two `<input>`s with no id both render as the selector `input`, so a
#: plan built from that cannot address them separately and drives the first one
#: twice. The walk up to the nearest id and then an nth-child path is the
#: ordinary way to build a unique selector, and it is valid CSS.
#: The selector set `ELEMENTS_JS` starts from. Named once because `settle`
#: has to watch exactly what the surface reads, or a page is
#: declared ready while its controls are still arriving. The surface reads
#: one thing more than this, the elements a pointer cursor marks as
#: clickable, and `STRUCTURE_JS` counts those into its hash for that reason.
PICK = ('img,a,button,input,select,textarea,h1,h2,canvas,'
        'video,form,table,section,[role=button],[onclick]')

#: The tags the pointer-cursor sweep is allowed to promote into a control.
#: Named once because `UNREACHED_JS` has to ask the same question from the
#: other side: anything these two disagree about is surface that is invisible
#: to the plan and invisible to the check that knows the plan is incomplete.
CLICKY = 'div,span,li,td,th,section,p'

#: Cursors that mean *take hold of this and move it*, as opposed to the click
#: `pointer` asks for. A split pane's bar carries `col-resize` and a sortable
#: row carries `move`, and neither is a click: pressing them does nothing at
#: all, which is exactly what they did when the sweep only knew `pointer`.
DRAGGY = ('col-resize', 'row-resize', 'ew-resize', 'ns-resize', 'nwse-resize',
          'nesw-resize', 'move', 'grab', 'grabbing', 'all-scroll')

#: How a canvas is read, whatever kind it is. Shared by the signature and by
#: the element sweep so the two cannot disagree about what a canvas holds.
#:
#: **A canvas has one context type for its whole life.** Ask a WebGL canvas
#: for a `2d` context and you get `null`, `getImageData` throws, and every
#: canvas rule here (painted, quiet, the second stroke) silently measures
#: nothing at all. A 3D program was invisible to this tool.
#:
#: The way through is `toDataURL`, with one catch that decides everything:
#: outside a frame it returns an image byte-identical to a blank canvas,
#: because the drawing buffer is cleared once it has been composited. Inside
#: `requestAnimationFrame` it still holds the frame. So the read is made
#: there, painted onto an ordinary 2d canvas, and measured exactly like any
#: other. Same numbers, same comparisons, nothing downstream knows.
CANVAS_JS = """
    const _measure = (d, w, ht) => {
        let n = 0, cx = 0, cy = 0, r = 0, g = 0, b = 0, h = 0;
        let rl = 255, rh = 0, gl = 255, gh = 0, bl = 255, bh = 0;
        for (let y = 0; y < ht; y++)
          for (let x = 0; x < w; x++) {
            const i = (y * w + x) * 4;
            if (d[i + 3] > 10) {
              n++; cx += x; cy += y;
              r += d[i]; g += d[i + 1]; b += d[i + 2];
              // **One colour edge to edge is not a picture.** A spread
              // rather than a palette, because it costs six comparisons and
              // no map, and paired with coverage below, because a black line
              // on a transparent canvas is also one colour: only the ink is
              // counted, so uniform alone cannot tell a stroke from a clear.
              if (d[i] < rl) rl = d[i]; if (d[i] > rh) rh = d[i];
              if (d[i+1] < gl) gl = d[i+1]; if (d[i+1] > gh) gh = d[i+1];
              if (d[i+2] < bl) bl = d[i+2]; if (d[i+2] > bh) bh = d[i+2];
            }
            h = (h * 31 + d[i] + d[i + 1] * 7 + d[i + 2] * 13
                 + d[i + 3] * 17) | 0;
          }
        const spread = n ? (rh - rl) + (gh - gl) + (bh - bl) : 0;
        const flat = (n > 0 && spread === 0 && n === w * ht) ? 1 : 0;
        return n ? [n, Math.round(cx / n), Math.round(cy / n),
                    Math.round(r / n), Math.round(g / n),
                    Math.round(b / n), h, flat]
                 : [0, 0, 0, 0, 0, 0, h, 0];
    };
    const _blind = [-1, -1, -1, -1, -1, -1, -1, -1];
    const _pixels = async (c) => {
        if (!c.width || !c.height) return _blind;
        let ctx = null;
        try { ctx = c.getContext('2d'); } catch (e) { ctx = null; }
        if (ctx) {
            try {
                return _measure(ctx.getImageData(0, 0, c.width, c.height).data,
                                c.width, c.height);
            } catch (e) { return _blind; }
        }
        try {
            const url = await new Promise((ok, no) => {
                const t = setTimeout(() => no(new Error('no frame')), 2000);
                requestAnimationFrame(() => { clearTimeout(t); ok(c.toDataURL()); });
            });
            const img = new Image();
            await new Promise((ok) => { img.onload = ok; img.onerror = ok;
                                        img.src = url; });
            const off = document.createElement('canvas');
            off.width = c.width; off.height = c.height;
            const octx = off.getContext('2d');
            octx.drawImage(img, 0, 0);
            return _measure(octx.getImageData(0, 0, off.width, off.height).data,
                            off.width, off.height);
        } catch (e) { return _blind; }
    };
"""


ELEMENTS_JS = """async () => {
__CANVAS__    const pending = [];
    const unique = (el) => {
        if (el.id) return '#' + CSS.escape(el.id);
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1 && node !== document.body) {
            if (node.id) { parts.unshift('#' + CSS.escape(node.id)); break; }
            const parent = node.parentElement;
            if (!parent) { parts.unshift(node.tagName.toLowerCase()); break; }
            const k = Array.prototype.indexOf.call(parent.children, node) + 1;
            parts.unshift(node.tagName.toLowerCase() + ':nth-child(' + k + ')');
            node = parent;
        }
        return parts.join(' > ') || el.tagName.toLowerCase();
    };
    // The smallest ancestor holding a field *and* a button is the widget the
    // two of them make up. Controls sharing one belong together; controls in
    // different ones do not, however alike they look. Three "New card…"
    // boxes beside three "+" buttons are three widgets, not one.
    const groups = [], pairs = [];
    const groupOf = (el) => {
        let node = el.parentElement;
        while (node && node !== document.body) {
            if (node.querySelector('input,textarea,select')
                && node.querySelector('button,[role=button],input[type=submit]')) {
                const at = groups.indexOf(node);
                if (at >= 0) return at + 1;
                groups.push(node);
                return groups.length;
            }
            node = node.parentElement;
        }
        return 0;
    };
    // **A pointer cursor is the page saying "click this."** A grid built
    // from divs has its handler attached in JavaScript, and a listener
    // cannot be read from the DOM, so a tic-tac-toe board, a minesweeper
    // field and a paint grid all measured as a page whose only control is
    // its Reset button, and the game itself was never once clicked.
    //
    // The rule was already written down here and applied only to counting
    // whether the page is alive. Same rule, two places, and it reached one
    // of them. Innermost only: a container styled `cursor: pointer` around
    // real cells is one element pretending to be the board.
    const picked = new Set(document.querySelectorAll(__PICK__));
    // Editable regions and drag handles, neither of which any tag announces.
    const grabby = new Set(__DRAGGY__);
    const editable = [...document.querySelectorAll('[contenteditable]')]
        .filter(el => el.getAttribute('contenteditable') !== 'false'
                      && !picked.has(el));
    const handles = [...document.querySelectorAll('*')].filter(el => {
        if (picked.has(el) || editable.includes(el)) return false;
        if (el.getAttribute('draggable') === 'true') return true;
        return grabby.has(getComputedStyle(el).cursor);
    }).filter(el => {
        const r = el.getBoundingClientRect();
        return r.width > 2 && r.height > 2;
    }).slice(0, 40);
    const cells = [];
    for (const el of document.querySelectorAll(__CLICKY__)) {
        if (picked.has(el) || cells.length > 400) continue;
        if (getComputedStyle(el).cursor !== 'pointer') continue;
        if (el.querySelector('*') && Array.from(el.querySelectorAll('*'))
                .some(k => getComputedStyle(k).cursor === 'pointer')) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 6 || r.height < 6) continue;
        cells.push(el);
    }
    const out = Array.from(picked).concat(editable).concat(handles)
        .concat(cells).slice(0, 250).map(el => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        const o = {
            tag: el.tagName.toLowerCase(),
            sel: unique(el),
            w: Math.round(r.width), h: Math.round(r.height),
            vis: cs.display !== 'none' && cs.visibility !== 'hidden'
                 && cs.opacity !== '0' && r.width > 0 && r.height > 0,
            text: (el.innerText || '').slice(0, 120)
        };
        const t = (el.getAttribute('type') || '').toLowerCase();
        if (o.tag === 'button' || t === 'button' || t === 'submit'
            || t === 'reset' || el.getAttribute('role') === 'button') {
            o.kind = 'button';
        } else if (o.tag === 'select') { o.kind = 'select';
        } else if (o.tag === 'textarea') { o.kind = 'text';
        } else if (o.tag === 'input') {
            o.kind = (t === 'checkbox' || t === 'radio' || t === 'range'
                      || t === 'number' || t === 'file' || t === 'color')
                     ? t : 'text';
        } else if (o.tag === 'a' && el.getAttribute('href')) {
            o.kind = 'link';
        } else if (o.tag === 'canvas') { o.kind = 'canvas';
        // **An element the page made editable is a text box without the
        // tag.** A spreadsheet of contentEditable cells and a diff viewer
        // with two editable panes both measured as a page whose only control
        // was one button, and assay pressed that button against panes it had
        // never typed into and called the page dead.
        } else if (el.isContentEditable) { o.kind = 'text';
        // **A handle is grasped, not pressed.** Clicking a split pane's bar
        // or a draggable row does nothing whatever, so a surface that only
        // knows how to click had no way to exercise either.
        } else if (handles.includes(el)) {
            o.kind = 'handle';
            o.grabbed = el.getAttribute('draggable') === 'true';
        } else if (cells.includes(el)) { o.kind = 'cell'; }
        if (o.kind) {
            // A label's own words are its direct text nodes. Everything
            // nested inside it belongs to something else: the options of a
            // select it wraps, the live value in a span beside a slider.
            // Read whole, `<label>Size: <select>` named a control
            // "Size: Small Medium Large" across four lines and a slider
            // "Red: 0", with the 0 changing as it moved.
            const own = node => Array.from(node.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent).join(' ')
                .replace(/\\s+/g, ' ').replace(/[:\\s]+$/, '').trim();
            const labelEl = el.labels && el.labels[0] ? el.labels[0] : null;
            const lab = labelEl
                ? (own(labelEl) || (labelEl.innerText || '').trim()) : '';
            // A select's own text is its options, which name nothing.
            const self = o.tag === 'select' ? '' : (el.innerText || '').trim();
            o.label = (el.getAttribute('aria-label') || lab || self
                       || el.getAttribute('placeholder')
                       || el.getAttribute('title')
                       || el.getAttribute('value')
                       || el.id || '')
                .replace(/\\s+/g, ' ').trim().slice(0, 60);
            o.enabled = !el.disabled && !el.hasAttribute('aria-disabled');
        }
        if (o.tag === 'img') {
            o.loaded = el.complete && el.naturalWidth > 0;
            o.src = el.getAttribute('src') || '';
        }
        if (o.tag === 'canvas') pending.push(
            _pixels(el).then(p => { o.painted = p[0]; }));
        if (o.kind) o.group = groupOf(el);
        o.readonly = !!(el.readOnly || el.hasAttribute('readonly'));
        const form = el.closest('form');
        const holder = form || el.parentElement;
        if (holder) {
            const seen = pairs.indexOf(holder);
            o.pairing = seen >= 0 ? seen + 1 : pairs.push(holder);
        }
        return o;
    });
    await Promise.all(pending);
    return out;
}""".replace("__PICK__", repr(PICK)).replace("__CLICKY__", repr(CLICKY)) \
     .replace("__DRAGGY__", repr(list(DRAGGY))).replace("__CANVAS__", CANVAS_JS)

#: What the page is showing, in the few numbers that can be compared against
#: themselves before and after an action. Each term is here because something
#: else missed a real change:
#:
#: * **painted count and centroid** tell "the piece moved" from "nothing
#:   happened", and separate gravity from a keypress on a page that animates.
#: * **mean colour** because a whole class of program changes nothing else:
#:   repainting an opaque cell a different opaque colour leaves the count, the
#:   centroid, the text and the element count all identical.
#: * **an exact pixel hash** because the mean is too coarse to see a brush
#:   stroke. One stroke on a 640x480 opaque canvas moves the rounded mean by
#:   less than 1, and a paint tool that demonstrably paints reported nothing.
#: * **a hash over every style and class** because a grid built from DOM
#:   elements paints a cell by setting its `style`: same text, same element
#:   count, no canvas to measure.
SIGNATURE_JS = """async () => {
__CANVAS__    return {
    canvas: await Promise.all(
        Array.from(document.querySelectorAll('canvas')).map(_pixels)),
    text: (document.body.innerText || '').slice(0, 400),
    // **What is in the fields is part of what the page is showing.** It is
    // not in `innerText`, not in the styles and not on a canvas, so a page
    // whose whole answer lands in an input was invisible: a converter that
    // puts 212 in the other box, a generator that fills a field, a form that
    // echoes what you typed. Three programs verified by hand to work were
    // reported broken with *nothing on the page changed at all*, and the
    // page had changed, and assay was looking everywhere except the boxes.
    fields: (() => {
        let h = 0;
        for (const el of document.querySelectorAll('input,textarea,select')) {
            const s = el.type === 'checkbox' || el.type === 'radio'
                ? String(el.checked) : String(el.value);
            for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
        }
        return h;
    })(),
    elements: document.querySelectorAll('*').length,
    styles: (() => {
        let h = 0;
        for (const el of document.querySelectorAll('*')) {
            const s = (el.getAttribute('style') || '') + '|'
                    + (typeof el.className === 'string' ? el.className : '');
            for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
        }
        return h;
    })(),
    };
}""".replace("__CANVAS__", CANVAS_JS)


#: What the page offers, reduced to one number, plus how many working
#: controls are on it.
#:
#: The hash is deliberately **not** over text or pixels: a clock rewrites its
#: text every second and an animation loop repaints every frame, and a page
#: doing either is working perfectly. What has to stop moving before the
#: surface can be measured is the set of controls, their labels and whether
#: they are enabled, so that is what it covers.
#:
#: `live` is the second half, and without it the first half is not enough: a
#: spinner is perfectly still. See `settle`.
STRUCTURE_JS = """() => {
    let h = 0, live = 0;
    const eat = (s) => {
        for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    };
    eat(String(document.querySelectorAll('*').length));
    for (const el of Array.from(document.querySelectorAll(__PICK__)).slice(0, 250)) {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        eat(el.tagName + '|' + (el.id || '') + '|'
            + (typeof el.className === 'string' ? el.className : '') + '|'
            + (el.innerText || '').slice(0, 120) + '|'
            + (el.disabled ? '1' : '0') + '|'
            + Math.round(r.width) + 'x' + Math.round(r.height) + '|'
            + (cs.display !== 'none' && cs.visibility !== 'hidden'
               && cs.opacity !== '0' && r.width > 0 && r.height > 0));
    }
    // **The hash covers the cells too, because the surface now reads them.**
    // `PICK` and the pointer-cursor sweep together are what a plan is built
    // from, and a hash over only half of that declares a board ready while
    // its cells are still being appended. The count is enough, because a cell's
    // text changes as the game is played, and hashing that would mean a
    // page in play never looks settled.
    let named = 0, pointing = 0;
    const working = (el) => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return cs.display !== 'none' && cs.visibility !== 'hidden'
            && cs.opacity !== '0' && r.width > 0 && r.height > 0
            && !el.disabled;
    };
    for (const el of document.querySelectorAll(
             'button,input,select,textarea,a[href],canvas,[role=button],[onclick]'))
        if (working(el)) {
            live++;
            // A canvas is deliberately not a *named* control. An empty one is
            // exactly what a dead page has, so counting it as something to
            // work would excuse the page it is the only thing on.
            if (el.tagName !== 'CANVAS') named++;
        }
    // **An editable region is a text box to the surface, so it is one here.**
    // Left out, a sheet of `contentEditable` cells reads as nothing to work,
    // and every open is watched to the ceiling.
    for (const el of document.querySelectorAll('[contenteditable]'))
        if (el.getAttribute('contenteditable') !== 'false' && working(el)) {
            live++;
            named++;
        }
    // **A pointer cursor is the page saying "click this".** A grid is
    // routinely 81 plain divs with one handler on their parent, and a
    // listener cannot be seen from here. `cursor: pointer` can be, and it
    // means exactly this. Without it a whole minesweeper read as an empty
    // page: no text, no canvas, no button, and 81 things to click.
    // A grab or resize cursor, or `draggable`, says "take hold of this", and
    // the surface drives those as handles, so they are controls here too.
    const grabby = new Set(__DRAGGY__);
    for (const el of document.querySelectorAll(__CLICKY__ + ',a')) {
        const cursor = getComputedStyle(el).cursor;
        if (cursor !== 'pointer' && !grabby.has(cursor)) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) pointing++;
    }
    for (const el of document.querySelectorAll('[draggable=true]')) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) pointing++;
    }
    eat('cells:' + pointing);

    // Anything a person would see at all, which is the question `live` does
    // not ask.
    // A page of nothing but prose offers no control and is not blank.
    let shown = (document.body ? (document.body.innerText || '').trim().length
                               : 0);
    for (const im of document.querySelectorAll('img'))
        if (im.naturalWidth > 0) shown += 1;
    for (const c of document.querySelectorAll('canvas')) {
        try {
            const d = c.getContext('2d')
                       .getImageData(0, 0, c.width, c.height).data;
            for (let i = 3; i < d.length; i += 4)
                if (d[i] > 10) { shown += 1; break; }
        } catch (e) { shown += 1; }   // unreadable is not empty
    }
    // **`live` is what `settle` waits for, so it has to mean the same thing
    // the surface means by a control.** It counted form controls only, and a
    // memory board of sixty-four clickable divs therefore reported nothing
    // to work, so a page that had finished arriving was watched to the
    // ceiling every single time it was opened, fifteen seconds a load, on
    // sixteen programs here. The readiness rule is still exactly what it
    // was, quiet counts only once there is something to work, and what
    // changed is that a cell is now one of those things, which is the same
    // correction `ELEMENTS_JS` just had.
    return {h: h, live: live + pointing, named: named + pointing,
            shown: shown};
}""".replace("__PICK__", repr(PICK)).replace("__CLICKY__", repr(CLICKY)) \
     .replace("__DRAGGY__", repr(list(DRAGGY)))


class Settled(NamedTuple):
    """How a page came to rest, as three separate facts.

    Collapsing them loses the distinction that matters: a page still moving,
    a page that has stopped and offers nothing to work, and a page that
    rendered nothing at all are three different things, and only the last is
    a fault on its own.
    """

    #: Whether the structure stopped changing.
    quiet: bool
    #: Working controls on it at the end. Zero is why an empty page is watched
    #: to the ceiling rather than measured the moment it stops moving.
    live: int
    #: The same count without canvases. A page whose only control is a canvas
    #: nobody has drawn in has nothing on it, and `live` alone would excuse
    #: exactly the dead page this is meant to catch.
    named: int
    #: Whether anything at all was rendered: text, a loaded image, a canvas
    #: with paint. Zero here is a blank page, which no correct program is,
    #: but only when `measured` is true.
    shown: int
    #: How long the watching took.
    ms: int
    #: Whether a single reading ever came back. A page can put the instrument
    #: out rather than be empty: one generated calculator declares
    #: `function eval()`, replacing the global the driver evaluates through,
    #: so every reading returns nothing. That page works, it computes
    #: 7 + 3 = 10, and calling it blank would be the one mistake this whole
    #: tool exists to avoid, a check that could not run reading exactly like
    #: one that failed.
    measured: bool = True


def settle(page: Any, poll_ms: int = 100, stable: int = 3,
           ceiling_ms: int = 15000) -> "Settled":
    """Wait while the surface is still arriving. Stop when it is not.

    A fixed pause cannot tell a framework that mounts in 80ms from one that
    mounts after a round trip, and it ends both the same way, which is how a
    page still showing *Loading…* came to be measured as a program offering no
    controls at all, and reported as working.

    So nothing is waited *for*; what is watched is whether anything is still
    changing. With one qualification that the first version of this lacked and
    which is the whole difficulty: **a page can be perfectly still and not be
    finished.** A spinner does not move. Three quiet polls over a page holding
    one `Loading…` is exactly what a mounted, working page looks like, and
    measuring there gives a surface with nothing on it. So quiet is only taken
    as readiness once the page offers *something* to work. Until then the
    only honest reading of an empty page is that it may still be coming, and
    it is watched to the ceiling.

    Returns whether it settled and how long that took. A page that never
    settles is a real and ordinary thing (a growing feed, a carousel, and
    equally an app that renders nothing at all) so hitting the ceiling is
    **reported, never failed on** here: what is on the page at that moment is
    still the best measurement available, and calling a working page broken
    costs more than the missing certainty. Whether an empty one is a fault is
    a question for the surface, which is the thing that can see it is empty.
    """
    seen: Any = None
    same, waited = 0, 0
    read_one = False
    while waited < ceiling_ms:
        try:
            now = page.evaluate(STRUCTURE_JS)
        except Exception:
            # Mid-navigation, or the page went away. Not a verdict about the
            # program; give it another poll rather than declaring anything.
            now = None
        # A reading that came back at all, whatever it said. A page can put
        # the instrument out rather than be empty, and the two must not end
        # up as the same number.
        read_one = read_one or isinstance(now, dict)
        if isinstance(now, dict) and isinstance(seen, dict) \
                and now["h"] == seen["h"]:
            same += 1
            if same >= stable and now["live"]:
                return Settled(True, now["live"], now["named"],
                               now["shown"], waited, True)
        else:
            same = 0
        seen = now
        page.wait_for_timeout(poll_ms)
        waited += poll_ms
    got = seen if isinstance(seen, dict) else {}
    return Settled(bool(got) and same >= stable, got.get("live", 0),
                   got.get("named", 0), got.get("shown", 0), waited, read_one)


def _drag(page: Any, target: str) -> None:
    """Draw across an element with the mouse held down.

    A freehand canvas responds to nothing else. It is not clicked into life
    and it has no keys: the whole program is press, move, release, and a plan
    that only clicks and types reports a working drawing tool as a canvas
    that does not respond. Two working ones were called broken exactly here.

    The target may carry `@x,y` to say where the stroke starts. **A second
    stroke has to land somewhere the first did not**, or it retraces pixels
    that are already that colour and a working painter looks broken.
    """
    sel, _, spot = target.partition("@")
    box = page.query_selector(sel).bounding_box()
    x, y = box["x"], box["y"]
    w, h = box["width"], box["height"]
    try:
        fx, fy = (float(n) for n in spot.split(","))
    except ValueError:
        fx = fy = CANVAS_X
    # **A stroke walks away from the edge it starts near**, so it can never
    # leave the box. Walking one direction always, a stroke starting in the
    # far corner finishes outside the element, so the release lands on the
    # page instead of the canvas, a painter that commits on `mouseup` never
    # commits, and a working drawing tool measures as one that drew nothing.
    # That is how the second-stroke case first reported every painter broken.
    dx, dy = (-0.09 if fx > 0.5 else 0.09), (-0.07 if fy > 0.5 else 0.07)
    page.mouse.move(x + w * fx, y + h * fy)
    page.mouse.down()
    for step in range(1, 7):
        page.mouse.move(x + w * (fx + step * dx), y + h * (fy + step * dy))
        page.wait_for_timeout(40)
    page.mouse.up()
    page.wait_for_timeout(150)


def answer_dialogs(page: Any) -> None:
    """Answer what the page asks, instead of dismissing it.

    A driver's default is to dismiss every `prompt`, `confirm` and `alert`,
    and a page that asks for the card's title through one then correctly
    adds nothing. Three working kanban boards here measured as pages where
    no button does anything, because the question was never answered.

    Dismissing is not the neutral choice it looks like. It is answering
    *no* to everything, which is exactly the answer that makes a feature not
    happen. Accepting is what a person testing the program does: they are
    trying to see the thing work, and a `confirm` they agree to is a button
    that did what it said.

    The value follows the same reading of the words that a text field gets,
    because `Sample item` is not an answer to *How many?*.
    """
    def answer(dialog: Any) -> None:
        with contextlib.suppress(Exception):
            if dialog.type == "prompt":
                dialog.accept(sample_for(dialog.message))
            else:
                dialog.accept()
    page.on("dialog", answer)


def sample_for(words: str) -> str:
    """A plausible answer to a question, read off the words asking it.

    Shared with the plan's own `_typed_for` so a `prompt` asking for a
    number and a field asking for one get the same answer, because two places
    deciding what to type is two places to disagree.
    """
    name = (words or "").lower()
    if "mail" in name:
        return "someone@example.com"
    # **A box asking for an address is not answered by a sentence.** A
    # bookmark manager validates what it is given with `new URL(...)`,
    # correctly refuses `Sample item`, adds nothing, and was reported for
    # not changing. The page was right and the answer was rubbish.
    if any(word in name for word in ("url", "link", "http", "website",
                                     "web address", "site")):
        return "https://example.com/page"
    if any(word in name for word in
           ("number", "digit", "amount", "price", "qty", "quantity",
            "age", "year", "second", "minute", "value", "how many")):
        return "5"
    return "Sample item"


#: Boxes whose own placeholder fails their own `pattern`.
#:
#: **A box whose own example fails its own rule can never be filled.** One
#: wizard here carries `pattern="\\d{5}"` on its postcode: an escaped
#: backslash, so the rule matches a literal backslash followed by five letter
#: d's, no postcode passes, and the step it sits on can never be completed.
#:
#: Nothing that drives the page can see it, which is why this is read rather
#: than driven: the field is on a later step, off screen, so it is not in the
#: surface to be typed into and the step before it advances perfectly well.
#: The placeholder is the page's own worked example, so a page whose example
#: fails its own validation is contradicting itself, and that is a fact about
#: the page rather than an opinion about its design.
#:
#: Asked of a detached copy so the real input is never written to, and using
#: the browser's own validator rather than a second reading of what `pattern`
#: means. Skipped where the placeholder carries a space, because then it is
#: an instruction rather than an example and proves nothing either way.
UNFILLABLE_JS = """() =>
    Array.from(document.querySelectorAll('input[pattern][placeholder]'))
      .map(el => {
        const pat = el.getAttribute('pattern');
        const eg = el.getAttribute('placeholder');
        if (!pat || !eg || eg.indexOf(' ') >= 0) return null;
        try {
            const probe = document.createElement('input');
            probe.setAttribute('pattern', pat);
            probe.value = eg;
            if (probe.checkValidity()) return null;
            return {name: el.name || el.id || el.type || 'a box',
                    pattern: pat, example: eg};
        } catch (e) { return null; }
      }).filter(Boolean)"""


def unfillable(page: Any) -> List[Dict[str, str]]:
    """Boxes the page's own example cannot satisfy. See `UNFILLABLE_JS`."""
    try:
        got = page.evaluate(UNFILLABLE_JS)
        return got if isinstance(got, list) else []
    except Exception:
        return []


def rendered(page: Any) -> Optional[Dict[str, int]]:
    """What the page is showing right now: content, and things to work.

    One reading of the same measurement `settle` watches. `None` means the
    reading did not come back, which is not the same as nothing being there.
    """
    try:
        got = page.evaluate(STRUCTURE_JS)
    except Exception:
        return None
    if not isinstance(got, dict):
        return None
    return {"shown": int(got.get("shown") or 0),
            "named": int(got.get("named") or 0),
            "live": int(got.get("live") or 0)}


class Rested(NamedTuple):
    """How a canvas came to a stop, and whether it was ever going.

    The two are separate because only together do they mean anything. Quiet
    and never moving is an ordinary still picture; quiet **after moving** is a
    program that ran and reached a state of its own, and what it does next is
    not evidence about whether it was ever wired.
    """

    quiet: bool
    #: Whether it was still changing when the watch began.
    moved: bool


def settle_canvas(page: Any, poll_ms: int = 200, stable: int = 3,
                  ceiling_ms: int = 4000) -> Rested:
    """Wait for the canvases to stop changing on their own. Did they?

    The separator between *the program is alive* and *the program responded to
    me*. A canvas case compares the page before a gesture to the page after it,
    and a game that animates by itself moves in that window whether or not
    anything was pressed. One snake here plays itself for two seconds, dies
    with `Press Space to restart`, ignores Space, and passed every case because
    it was measured while the corpse was still twitching.

    So the canvas is brought to rest first. A program still moving when the
    ceiling arrives is alive and nothing can be attributed to a gesture, so the
    caller leaves it alone; one that has gone quiet is a program where what
    happens next is down to what was done to it.

    The ceiling is the one number here that ends something, and it measures
    exactly what it is allowed to: whether the canvas is still producing
    frames. It is not a bound on how long a case may take.
    """
    seen, still, waited, moved = None, 0, 0, False
    while waited <= ceiling_ms:
        now = (signature(page) or {}).get("canvas")
        if now is None:
            return Rested(False, moved)
        if seen is not None and now != seen:
            moved = True
        still = still + 1 if now == seen else 0
        if still >= stable:
            return Rested(True, moved)
        seen = now
        page.wait_for_timeout(poll_ms)
        waited += poll_ms
    return Rested(False, moved)


#: What the page offers that the surface rules did not pick up.
#:
#: **A page-wide verdict is only as good as the sample it was drawn from.**
#: The claim that nothing here is wired is the most expensive thing this tool
#: says, and it is made from whatever the plan happened to reach. On a
#: sortable table the plan reached twenty-four data cells and none of the
#: three headers, pressed all twenty-four, and announced that the page
#: answers nothing. It was right about the cells and wrong about the page.
#:
#: So the rule needs the other half of the picture: is there anything here
#: that plainly does something, which I did not include? Three things say
#: that without a listener being readable: a cursor the page went out of its
#: way to change, `contenteditable`, and `draggable`. None of them proves the
#: element works. All of them prove the plan is not the whole page.
#:
#: It counts what is **left over**, never how much was found. Small and
#: complete is a real answer: a spreadsheet whose script died before building
#: a single cell offers nothing, and nothing is what should be reported.
UNREACHED_JS = """() => {
    const seen = (el) => { const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return r.width > 6 && r.height > 6 && cs.display !== 'none'
            && cs.visibility !== 'hidden' && cs.opacity !== '0'; };
    // Exactly what the plan is built from, asked the same way.
    const reached = new Set(document.querySelectorAll(__PICK__));
    for (const el of document.querySelectorAll(__CLICKY__)) {
        if (reached.has(el)) continue;
        if (getComputedStyle(el).cursor !== 'pointer') continue;
        if (el.querySelector('*') && Array.from(el.querySelectorAll('*'))
                .some(k => getComputedStyle(k).cursor === 'pointer')) continue;
        if (seen(el)) reached.add(el);
    }
    const out = {};
    const note = (el, why) => {
        if (reached.has(el) || !seen(el)) return;
        out[why] = (out[why] || 0) + 1;
    };
    for (const el of document.querySelectorAll('[contenteditable]'))
        if (el.getAttribute('contenteditable') !== 'false')
            note(el, 'contenteditable');
    for (const el of document.querySelectorAll('[draggable=true]'))
        note(el, 'draggable');
    for (const el of document.querySelectorAll('*'))
        if (__GRABBY__.includes(getComputedStyle(el).cursor)) note(el, 'handle');
    // A cursor the author changed is the page pointing at something. The
    // ones skipped here are the page saying the opposite, or saying nothing:
    // `text` is a caret over prose, and `not-allowed` and `wait` are a
    // refusal. `pointer` is absent because the sweep above already has it,
    // and anything still carrying it is genuinely left over.
    for (const el of document.querySelectorAll('*')) {
        const c = getComputedStyle(el).cursor;
        if (['auto', 'default', 'text', 'none', 'not-allowed', 'wait',
             'progress', 'help', 'inherit'].includes(c)) continue;
        note(el, c);
    }
    return out;
}""".replace("__PICK__", repr(PICK)).replace("__CLICKY__", repr(CLICKY)) \
     .replace("__GRABBY__", repr(list(DRAGGY)))


def unreached(page: Any) -> Dict[str, int]:
    """Interactive-looking elements the plan was never going to touch.

    Empty means the plan saw everything the page advertises, which is what
    makes a page-wide verdict fair. Anything in it means the opposite.
    """
    try:
        return dict(page.evaluate(UNREACHED_JS))
    except Exception:
        # Never worth failing a run over: an empty answer costs one page-wide
        # finding and inventing one costs a program called broken.
        return {}


def elements(page: Any) -> List[Element]:
    """Every control the page rendered, measured rather than parsed.

    From the rendered page and not the markup: a control the page builds at
    run time is as real as one written in the HTML, and one the CSS hides is
    not there at all.
    """
    try:
        rows = page.evaluate(ELEMENTS_JS)
    except Exception:
        return []
    # A page that has replaced what the driver evaluates through answers with
    # whatever it likes: an int, a string, nothing. Only a list of mappings
    # is an answer; anything else is the instrument being out, and iterating
    # it raises in the middle of a measurement.
    if not isinstance(rows, list):
        return []
    rows = [r for r in rows if isinstance(r, dict)]
    return [
        Element(
            tag=str(r.get("tag") or ""), selector=str(r.get("sel") or ""),
            width=int(r.get("w") or 0), height=int(r.get("h") or 0),
            visible=bool(r.get("vis", True)), text=str(r.get("text") or "")[:120],
            kind=str(r.get("kind") or ""), label=str(r.get("label") or "")[:60],
            enabled=bool(r.get("enabled", True)),
            group=int(r.get("group") or 0),
            pairing=int(r.get("pairing") or 0),
            readonly=bool(r.get("readonly", False)),
            grabbed=bool(r.get("grabbed", False)),
            painted=r.get("painted"), loaded=r.get("loaded"),
            src=str(r.get("src") or "")[:200],
        )
        for r in rows or []
    ]


#: Two things a page can say about itself that need no opinion about what
#: it is for. Asked together because each is one round trip and they are
#: wanted at the same moment: after a case has acted, with the page open.
#:
#: **Computed text.** `[object Object]` is a value printed where one of its
#: fields was wanted, `NaN` is arithmetic on something that was not a number,
#: `undefined` is a name read before anything was put in it. None is typed on
#: purpose. `null` is deliberately absent: a table showing a database value
#: says it legitimately, and a rule that cannot tell those apart fires on
#: correct pages.
#:
#: **Wiring.** Two choices in one group carrying the same value, so one can
#: never be the answer. Two labels pointing at one control, which leaves
#: another with none. A label pointing at nothing, so clicking its words does
#: nothing. All three parse, render, and are wrong.
#:
#: **A page saying it is empty while it is showing something was tried here
#: and removed.** A shopping cart says *"Your basket is empty"* beside the
#: catalogue it is asking you to add from, and nothing mechanical can tell
#: which list a sentence is about. It cost two working programs and caught
#: nothing in two hundred and seventy-five.
FACTS_JS = r"""() => {
    const body = document.body ? (document.body.innerText || '') : '';
    const boxes = Array.from(document.querySelectorAll('input, textarea'))
        .map(el => el.value || '').join(' \n ');
    const all = body + ' \n ' + boxes;

    const computed = [];
    for (const token of ['NaN', '[object Object]', 'undefined']) {
        const at = all.indexOf(token);
        if (at < 0) continue;
        computed.push({
            token: token,
            around: all.slice(Math.max(0, at - 30), at + token.length + 30)
                       .replace(/\s+/g, ' ').trim()});
    }

    const wiring = [];
    const groups = {};
    for (const el of document.querySelectorAll('input[type=radio][name]')) {
        (groups[el.name] = groups[el.name] || []).push(el);
    }
    for (const name of Object.keys(groups)) {
        const seen = {};
        for (const el of groups[name]) {
            if (seen[el.value]) {
                wiring.push('two choices named "' + name + '" both carry the '
                    + 'value "' + el.value + '", so one of them can never be '
                    + 'the answer');
                break;
            }
            seen[el.value] = 1;
        }
    }
    const pointed = {};
    for (const lab of document.querySelectorAll('label[for]')) {
        const at = lab.getAttribute('for');
        const words = (lab.innerText || '').trim().slice(0, 24);
        if (!document.getElementById(at)) {
            wiring.push('a label reading "' + words + '" points at "' + at
                + '", which is not on the page');
        } else if (pointed[at]) {
            wiring.push('two labels both point at "' + at + '", so whatever'
                + ' the other control was called cannot be reached by its'
                + ' words');
        }
        pointed[at] = 1;
    }

    return {computed: computed, wiring: wiring};
}"""


#: How many things are on show, and every number the page is displaying on
#: its own. Together these answer whether a number is *about* the list: one
#: that moves with it one for one is tracking it, and the page has said so by
#: moving them together.
#:
#: A number is a leaf holding nothing but an integer. Anything with a child
#: is a container and its text is somebody else's; anything with a decimal
#: point is a measurement rather than a count, and money is exactly the thing
#: a count must not be confused with.
COUNTED_JS = r"""() => {
    const _attrs = el => Array.from(
            el.querySelectorAll('[href], [title], [value]'))
        .map(one => [one.getAttribute('href'), one.getAttribute('title'),
                     one.getAttribute('value')].join(' ')).join(' ');
    const shown = el => {
        const box = el.getBoundingClientRect();
        return box.width > 0 && box.height > 0
            && getComputedStyle(el).visibility !== 'hidden';
    };
    const operable = 'button, a, input, select, textarea, [role=button]';

    // **What a list is cannot be decided from one reading of it.** A
    // bookmark manager holding a single row has one element of its class,
    // which looks like nothing at all; the same page after two saves has
    // two. So every class is reported with how many of it are on show, and
    // which of them are lists is settled across the whole run, where the
    // list has been seen at more than one size.
    const classes = {};
    const texts = {};
    let rows = 0;
    let rowText = '';
    for (const el of document.querySelectorAll('li, tbody tr, [class]')) {
        if (!shown(el) || el.matches(operable)) continue;
        if (getComputedStyle(el).cursor === 'pointer') continue;
        if (el.tagName === 'LI' || el.tagName === 'TR') {
            rows++;
            rowText += ' ' + (el.innerText || '') + ' ' + _attrs(el);
            continue;
        }
        const key = el.className;
        if (key && typeof key === 'string') {
            classes[key] = (classes[key] || 0) + 1;
            texts[key] = ((texts[key] || '') + ' ' + (el.innerText || '')
                          + ' ' + _attrs(el)).slice(0, 600);
        }
    }

    const where = el => {
        const steps = [];
        for (let at = el; at && at.tagName !== 'BODY'; at = at.parentElement) {
            if (at.id) { steps.unshift('#' + at.id); break; }
            const among = Array.from(at.parentElement
                ? at.parentElement.children : []).indexOf(at);
            steps.unshift(at.tagName + ':' + among);
        }
        return steps.join('>');
    };
    const numbers = [];
    const holders = 'span, b, strong, td, div, p, em, h1, h2, h3';
    for (const el of document.querySelectorAll(holders)) {
        if (el.children.length || !shown(el)) continue;
        const said = (el.innerText || '').trim();
        // **Two questions of one reading.** Whether a number *counts* the
        // list needs a whole number, because money is the exact thing a
        // count must not be confused with. Whether a number *follows* the
        // list needs only that it moved, and a running total is the
        // commonest thing that should.
        const whole = /^-?\d{1,6}$/.test(said);
        const anyNum = /^-?\d{1,9}(\.\d{1,4})?$/.test(said);
        if (!anyNum) continue;
        numbers.push({at: where(el), is: whole ? parseInt(said, 10) : null,
                      said: said});
    }
    return {rows: rows, classes: classes, numbers: numbers,
            texts: texts, rowText: rowText.slice(0, 600)};
}"""


#: The row a control sits in, and how many rows there are like it. A row is
#: the first ancestor that has siblings of its own shape, which is what makes
#: it one of several rather than part of the furniture.
ROW_JS = r"""(sel) => {
    const path = el => {
        const steps = [];
        for (let at = el; at && at.tagName !== 'BODY'; at = at.parentElement) {
            if (at.id) { steps.unshift('#' + at.id); break; }
            const among = Array.from(at.parentElement
                ? at.parentElement.children : []).indexOf(at);
            steps.unshift(at.tagName + ':' + among);
        }
        return steps.join('>');
    };
    const el = document.querySelector(sel);
    if (!el) return null;
    for (let at = el; at && at.tagName !== 'BODY'; at = at.parentElement) {
        const up = at.parentElement;
        if (!up) break;
        const alike = Array.from(up.children).filter(
            one => one.tagName === at.tagName
                && String(one.className) === String(at.className));
        if (alike.length < 2) continue;
        return {text: (at.innerText || '').replace(/\s+/g, ' ').trim(),
                many: alike.length, holder: path(up),
                shape: at.tagName + '.' + String(at.className),
                all: alike.map(one => (one.innerText || '')
                     .replace(/\s+/g, ' ').trim())};
    }
    return null;
}"""

#: The same rows again, found by where they were rather than by the control
#: that was pressed. **After a row goes, the control's selector may not lead
#: back to the list at all**: with one row left there are no siblings to
#: recognise, so walking up from the button lands on whatever grouping the
#: page has further out, and the count appears to *rise*.
ROWS_JS = r"""([holder, shape]) => {
    const steps = holder.split('>');
    let at = null;
    for (const step of steps) {
        if (step.charAt(0) === '#') {
            at = document.getElementById(step.slice(1));
        }
        else {
            const bits = step.split(':');
            const among = at ? at.children
                : (document.body ? document.body.children : []);
            at = among[parseInt(bits[1], 10)];
        }
        if (!at) return null;
    }
    const alike = Array.from(at.children).filter(
        one => one.tagName + '.' + String(one.className) === shape);
    return {many: alike.length,
            all: alike.map(one => (one.innerText || '')
                 .replace(/\s+/g, ' ').trim())};
}"""


def rows_now(page: Any, holder: str, shape: str) -> Optional[Dict[str, Any]]:
    """The rows in that container now, whatever happened to the control."""
    if not holder:
        return None
    try:
        got = page.evaluate(ROWS_JS, [holder, shape])
        return got if isinstance(got, dict) else None
    except Exception:
        return None


#: **A box that corrects what it is given was tried and removed.** A
#: quantity box with a maximum of ten, handed twenty-five, correctly holds
#: ten; a stepper restores its floor when it is emptied. Reading either as
#: the page losing what somebody wrote flagged four working programs and
#: caught nothing, because clamping is what a careful field does.
def row_of(page: Any, selector: str) -> Optional[Dict[str, Any]]:
    """Which row this control is in, and what the rest of them say."""
    if not selector:
        return None
    try:
        got = page.evaluate(ROW_JS, selector)
        return got if isinstance(got, dict) else None
    except Exception:
        return None


def counted(page: Any) -> Dict[str, Any]:
    """What is on show, and the whole numbers the page is displaying."""
    try:
        got = page.evaluate(COUNTED_JS)
        return got if isinstance(got, dict) else {}
    except Exception:
        return {}


#: Whether a string the driver typed is anywhere a reader could find it:
#: the visible text, the boxes, or the attributes a link carries.
SHOWS_JS = r"""(needles) => {
    const text = document.body ? (document.body.innerText || '') : '';
    const boxes = Array.from(document.querySelectorAll('input, textarea'))
        .map(el => el.value || '').join(' \n ');
    const carriers = '[href], [src], [title], [alt], [value]';
    const attrs = Array.from(document.querySelectorAll(carriers))
        .map(el => [el.getAttribute('href'), el.getAttribute('src'),
                    el.getAttribute('title'), el.getAttribute('alt'),
                    el.getAttribute('value')].join(' ')).join(' \n ');
    const all = text + ' \n ' + boxes + ' \n ' + attrs;
    return needles.filter(one => all.indexOf(one) < 0);
}"""


def missing_from(page: Any, needles: Sequence[str]) -> List[str]:
    """Which of these the page is not showing anywhere."""
    if not needles:
        return []
    try:
        return list(page.evaluate(SHOWS_JS, list(needles)) or [])
    except Exception:
        return []


def facts(page: Any) -> Dict[str, Any]:
    """What the page says about itself, needing no opinion about its
    purpose."""
    try:
        got = page.evaluate(FACTS_JS)
        return got if isinstance(got, dict) else {}
    except Exception:
        return {}


def signature(page: Any) -> Dict[str, Any]:
    """What the page is showing, for comparing against itself."""
    try:
        return page.evaluate(SIGNATURE_JS)
    except Exception:
        return {}


# --------------------------------------------------------------------------
# Acting
# --------------------------------------------------------------------------

#: jQuery's `:contains()`, which a model writes readily and no browser
#: implements, so a Delete button named `.note:contains('Buy milk') .delete`
#: could never be clicked whatever the program did. Playwright's `:has-text()`
#: means the same thing and works.
_CONTAINS = re.compile(r":contains\(([^)]*)\)")


def _where(page: Any, selector: str, spot: str = "") -> Dict[str, Any]:
    """Where inside an element to click.

    A canvas is clicked off-centre; see `CANVAS_X`. `spot` overrides it with
    an explicit `x,y` fraction, which is how a plan clicks one canvas at four
    different places instead of clicking it four times in the same spot.
    """
    try:
        el = page.query_selector(selector)
        if el is None:
            return {}
        if not spot and (el.evaluate("e => e.tagName") or "").lower() != "canvas":
            return {}
        box = el.bounding_box() or {}
        if not box.get("width") or not box.get("height"):
            return {}
        fx, fy = (CANVAS_X, CANVAS_Y)
        if spot:
            a, _, b = spot.partition(",")
            fx, fy = float(a), float(b)
        return {"position": {"x": box["width"] * fx, "y": box["height"] * fy}}
    except Exception:
        # Never let choosing a nicer point be the reason a click fails.
        return {}


def _found(page: Any, selector: str) -> bool:
    """Whether a selector names an element, rather than being words."""
    try:
        return page.query_selector(selector) is not None
    except Exception:
        return False


def _disabled(page: Any, selector: str) -> bool:
    """Whether the page has that control disabled.

    Playwright waits for actionability and times out on a disabled control,
    which reads identically to one that is missing, and a working program's
    Undo, correctly disabled with nothing to undo, is not a defect.
    """
    try:
        el = page.query_selector(selector)
        return bool(el) and bool(
            el.get_attribute("disabled") is not None
            or el.get_attribute("aria-disabled"))
    except Exception:
        return False


#: Where a slider sits and how far it can go, so the act can move it the
#: whole way rather than to a number somebody guessed.
_REACH_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const lo = Number(el.min === '' ? 0 : el.min);
    const hi = Number(el.max === '' ? 100 : el.max);
    const now = Number(el.value);
    return String(now - lo > hi - now ? lo : hi);
}"""


def _slide(page: Any, selector: str, timeout: float) -> None:
    """Move a slider as far as it goes from wherever it is sitting.

    **A `range` counted as surface and was never driven**, so a page of three
    sliders offered plenty to operate, none of it was operated, and the
    whole-page verdict concluded nothing on it responded to anything. It
    worked perfectly.

    The far end rather than a fixed number, because a slider already sitting
    at the number you chose does not move, and an act that changes nothing
    proves nothing. Filled rather than dragged: dragging lands wherever the
    pixels fall and two runs disagree, which is the one thing this must not
    do.
    """
    reach = page.evaluate(_REACH_JS, selector)
    if reach is None:
        raise ValueError(f"nothing at {selector}")
    page.fill(selector, reach, timeout=timeout)


def perform(page: Any, acts: Sequence[Dict[str, str]],
            timeout: float = 4000) -> Tuple[List[str], List[str]]:
    """Do each act in order. Returns what could not be done, and what was off.

    A target may carry `@x,y` to name a point as a fraction of the element's
    box. A click tries the selector first and then the words on the control,
    because `{"click": "Start"}` is what a person would go by and is not CSS.
    """
    could_not: List[str] = []
    was_off: List[str] = []
    for step in acts:
        for verb, raw in step.items():
            arg = _CONTAINS.sub(r":has-text(\1)", str(raw))
            try:
                if verb in ("click", "dblclick"):
                    sel, _, spot = arg.partition("@")
                    try:
                        page.click(sel, timeout=timeout, **_where(page, sel, spot))
                    except Exception:
                        # **Words are a second way to name a control, not a
                        # second chance to press it.** A selector that found
                        # its element and could not press it will not match
                        # as text, and asking costs a second full timeout.
                        if _found(page, sel):
                            raise
                        page.click(f"text={sel}", timeout=timeout)
                elif verb == "press":
                    page.keyboard.press(arg)
                elif verb == "fill":
                    sel, _, value = arg.partition("=")
                    page.fill(sel.strip(), value.strip(), timeout=timeout)
                elif verb == "drag":
                    _drag(page, arg)
                elif verb == "slide":
                    _slide(page, arg, timeout)
                elif verb == "dragonto":
                    # **A `draggable` element is not moved by mouse events.**
                    # HTML5 drag and drop runs on its own event family, and a
                    # press-move-release never raises `dragstart`, so a
                    # reorder list that works perfectly measures as a list
                    # that ignores being dragged. Playwright's own drag is
                    # the one that speaks that protocol.
                    src, _, dst = arg.partition(">>")
                    page.drag_and_drop(src.strip(), dst.strip(),
                                       timeout=timeout)
                elif verb == "wait":
                    page.wait_for_timeout(min(int(float(arg) * 1000), 10000))
                else:
                    continue
            except Exception as exc:
                target = str(raw).split("@")[0]
                if verb in ("click", "dblclick") and _disabled(page, target):
                    was_off.append(f"{verb} {raw}")
                else:
                    could_not.append(
                        f"{verb} {raw}: {str(exc).splitlines()[0][:120]}")
    if acts:
        with contextlib.suppress(Exception):
            # **The pointer is moved off before anything is measured.** A
            # canvas that draws a hover highlight repaints wherever the mouse
            # was left, and that is not a response to the click. It made a
            # grid whose two handlers double-toggle, so every click nets to
            # nothing, measure as though it had responded.
            page.mouse.move(1, 1)
            page.wait_for_timeout(500)
    return could_not, was_off


# --------------------------------------------------------------------------
# Comparing
# --------------------------------------------------------------------------

def changed(was: Dict[str, Any], now: Dict[str, Any]) -> str:
    """What moved, in the numbers a reader can act on, pass or fail.

    Reported either way, because *which way* a thing moved is a judgement the
    machine does not have: gravity moves a piece down and Left moves it left,
    and stating `centre (640, 320)->(640, 704)` lets a reader see for itself
    that pressing Left moved nothing sideways.
    """
    if not was or not now:
        return ""
    bits: List[str] = []
    for i, (a, b) in enumerate(zip(was.get("canvas") or [], now.get("canvas") or [])):
        if a == b:
            bits.append(f"canvas {i}: unchanged ({a[0]} painted px)")
        elif len(a) > 6 and len(b) > 6 and a[:6] == b[:6]:
            bits.append(f"canvas {i}: its pixels changed, by less than the "
                        f"painted count or mean colour can show ({a[0]} px)")
        else:
            said = (f"canvas {i}: {a[0]}->{b[0]} painted px, "
                    f"centre ({a[1]}, {a[2]})->({b[1]}, {b[2]})")
            if len(a) > 5 and len(b) > 5 and a[3:6] != b[3:6]:
                said += (f", mean colour rgb({a[3]}, {a[4]}, {a[5]})"
                         f"->rgb({b[3]}, {b[4]}, {b[5]})")
            bits.append(said)
    if was.get("text") != now.get("text"):
        bits.append("the visible text changed")
    elif was.get("text"):
        bits.append("the visible text is unchanged")
    if was.get("fields") != now.get("fields"):
        bits.append("what is in the fields changed")
    if was.get("styles") != now.get("styles"):
        bits.append("something on the page was restyled or recoloured")
    return "; ".join(bits)


def moved(was: Dict[str, Any], now: Dict[str, Any]) -> Optional[bool]:
    """Whether the page was measurably different afterwards.

    `None` when it cannot be told. Unknown must never become *did not move*:
    that fails a working page on a measurement that never happened.
    """
    if not was or not now:
        return None
    return was != now


def canvas_still(was: Dict[str, Any], now: Dict[str, Any]) -> bool:
    """Whether every canvas is byte-identical afterwards.

    The **exact** term decides this one, where `moved` compares the whole
    coarse signature: the question here is whether the canvas that was acted
    on responded at all, and rounding a brush stroke away answers it wrongly.
    """
    before, after = (was or {}).get("canvas"), (now or {}).get("canvas")
    if not before or not after or len(before) != len(after):
        return False

    def stamp(rows: Sequence[Any]) -> List[Any]:
        return [r[6] if isinstance(r, list) and len(r) > 6 else r for r in rows]

    return stamp(before) == stamp(after)


def unpainted(now: Dict[str, Any]) -> int:
    """How many canvases still have nothing drawn in them.

    A canvas is an element like any other (present, sized, visible) so a
    program that draws nothing into one measures identically to one that draws
    a board. `-1` is *could not be read* and is not empty.

    **One colour edge to edge is a canvas nobody drew into**, whatever its
    alpha, and that is the second half of this. Counting non-transparent
    pixels answers the question for a 2d canvas, which starts transparent, and
    gets it exactly backwards for a WebGL one, which starts at whatever colour
    it was cleared to. Three wireframe cubes drew twenty-four line indices
    every frame into a buffer that clipped every one of them away, and each
    reported 836,000 painted pixels out of 836,000: completely full, and
    showing nothing.

    **Edge to edge, and not merely one colour.** On a 2d canvas the background
    is transparent and only the ink is counted, so a black line is also a
    single colour, and uniformity on its own reported two working drawing
    tools as canvases nobody had drawn on. What separates a clear from a
    stroke is that the clear covers every pixel.
    """
    return sum(1 for row in (now or {}).get("canvas") or []
               if isinstance(row, list) and row
               and (row[0] == 0 or (len(row) > 7 and row[7] == 1)))


#: A key the page tells you to press, in its own visible text.
_TOLD = re.compile(r"\b(?:press|hit|tap)\s+(?:the\s+)?"
                   r"(space\s?bar|space|enter|return|escape|esc|any\s+key)\b",
                   re.I)

_NAMED_KEY = {"space": "Space", "spacebar": "Space", "space bar": "Space",
              "enter": "Enter", "return": "Enter",
              "escape": "Escape", "esc": "Escape"}


def told_to_press(text: str) -> str:
    """The key the page asks for, `*` for any of them, empty for silence.

    **A page that says what to press has written down its own contract.** It
    is the one thing that separates a program which finished from a program
    which is stuck: both sit there ignoring the keyboard, and only one of
    them put `Press Space to restart` on the screen and then ignored Space.

    Read off the rendered text, so it is what a person would have read.
    """
    found = _TOLD.search(text or "")
    if not found:
        return ""
    word = " ".join(found.group(1).lower().split())
    return "*" if word.startswith("any") else _NAMED_KEY.get(word, "")


def was_pressed(key: str, acts: Sequence[Dict[str, str]]) -> bool:
    """Whether the acts included the key the page asked for."""
    if not key:
        return False
    for step in acts or ():
        said = str(step.get("press", ""))
        if said and (key == "*" or said.lower() == key.lower()):
            return True
    return False


#: One element, closely enough to tell whether it answered. Its own markup
#: catches a class going on or off and the text inside it changing; the
#: painted properties catch a page that colours it directly.
#:
#: **And what happens just above it, because that is where a click often
#: lands.** A flashcard is flipped by putting a class on the card, and the
#: face you clicked is untouched: its markup, its colours and its box are
#: all exactly as they were, and the card turned over. Three ancestors is
#: what covers the wrappers these pages put around a clickable thing without
#: reaching so far that any change anywhere counts.
ITSELF_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const style = getComputedStyle(el);
    const bits = [el.outerHTML, style.backgroundColor, style.color,
                  style.borderColor, style.transform];
    let up = el.parentElement;
    for (let n = 0; n < 3 && up; n++, up = up.parentElement) {
        bits.push(up.className, up.getAttribute('style') || '',
                  getComputedStyle(up).transform);
    }
    return bits.join('|');
}"""


def itself(page: Any, selector: str) -> Optional[str]:
    """What the element the act named looks like, or None if it is not
    there."""
    if not selector:
        return None
    try:
        got = page.evaluate(ITSELF_JS, selector)
        return None if got is None else str(got)
    except Exception:
        return None


def aimed_at_canvas(acts: Sequence[Dict[str, str]]) -> bool:
    """Whether an act names a canvas as its target.

    The page-wide floor is a whole-*page* test and a page is free to respond
    somewhere else: one grid announced *"Row 1 Column 1 turned on"* into a live
    region on every click, so the text moved while the cell being announced did
    not. This narrows the canvas check to where the act itself said what it
    aimed at.
    """
    for step in acts or ():
        for verb, arg in step.items():
            if verb in ("click", "dblclick") and "canvas" in str(arg).lower():
                return True
    return False
