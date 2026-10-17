"""Open a page, measure it, and act on it.

This module only measures. It reports painted pixels, centroids, colours,
text and element counts, and `run` decides what they mean, so each
measurement can be tested on its own.
"""

from __future__ import annotations

import base64
import contextlib
import weakref
import http.server
import re
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import (Any, Dict, Iterator, List, NamedTuple, Optional,
                    Sequence, Tuple)

#: Where to click on a canvas when the act names no point, as fractions of
#: its box. `surface.SAFE_LOW` explains why it's off-centre.
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
    #: `button`, `text`, `checkbox`, `select`, `canvas`, `link` and so on, or
    #: empty for an element that isn't a control. The tag alone can't tell,
    #: because an `<input>` is a text box, checkbox, slider or button
    #: depending on its `type`.
    kind: str = ""
    label: str = ""
    enabled: bool = True
    #: Whether the box is readonly, which makes it an output.
    readonly: bool = False
    #: Whether a handle has `draggable="true"`. Those move through HTML5 drag
    #: events, not mouse events.
    grabbed: bool = False
    #: An `<input>`'s `type`. A date box and a week box take values in
    #: different formats and reject each other's.
    input_type: str = ""
    #: The `name` a radio shares with the rest of its group.
    radio: str = ""
    #: The tags and classes from this element up to the nearest ancestor with
    #: an id. See `links.attach`.
    family: str = ""
    #: Which form this control is in, or its parent element when it's in no
    #: form. A field and a button with the same value are paired.
    pairing: int = 0
    #: Which widget this control belongs to, numbered by the smallest
    #: ancestor holding both a field and a button. On a board with three
    #: columns, each column is its own group, so one column's field isn't
    #: paired with another column's button.
    group: int = 0
    painted: Optional[int] = None
    loaded: Optional[bool] = None
    src: str = ""


class Crash(str):
    """An uncaught exception's message, with the frame it was thrown from.

    Two handlers can fail with the same message for different reasons, so
    the frame is what tells two crashes apart.
    """

    frame: str = ""


#: The first stack frame that belongs to the page, without the loopback
#: origin, because the port changes on every run.
_FRAME = re.compile(r"\bat\b.*?(?:https?://[^/\s]+/)?([^\s()/]+:\d+:\d+)")


def crash(error: Any) -> Crash:
    """A `pageerror`'s message and where it was thrown."""
    said = Crash(str(error)[:200])
    for line in str(getattr(error, "stack", "") or "").splitlines()[1:]:
        found = _FRAME.search(line)
        if found:
            said.frame = found.group(1)
            break
    return said


# --------------------------------------------------------------------------
# Serving
# --------------------------------------------------------------------------

@contextlib.contextmanager
def serve(root: Path) -> Iterator[str]:
    """Serve a folder over http and yield its base URL.

    Pages are served instead of opened from disk, because a `file://` page
    can't load `<script type="module">`. The page still renders, but none of
    its module code runs.
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a: Any, **kw: Any) -> None:
            super().__init__(*a, directory=str(root), **kw)

        def send_head(self) -> Any:
            if not servable(root, Path(self.translate_path(self.path))):
                self.send_error(404)
                return None
            return super().send_head()

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


def servable(root: Path, path: Path) -> bool:
    """Whether `serve` may answer with `path`, a file or folder under `root`.

    The page under test can request any URL on the server and send what it
    reads anywhere, so the server keeps to the folder's own files. It refuses
    hidden files and folders, like `.env` and `.git/`, and a symlink that
    leads out of the folder.
    """
    try:
        inside = path.relative_to(root)
    except ValueError:
        return False
    if any(part.startswith(".") for part in inside.parts):
        return False
    return path.resolve().is_relative_to(root.resolve())


# --------------------------------------------------------------------------
# Measuring
# --------------------------------------------------------------------------

#: The elements a plan is built from. `settle` hashes the same set, so a page
#: isn't declared ready while these are still arriving. The surface also
#: reads elements with a pointer cursor, and `STRUCTURE_JS` counts those
#: separately for the same reason.
PICK = ('img,a,button,input,select,textarea,h1,h2,canvas,'
        'video,form,table,section,[role=button],[onclick]')

#: The tags the pointer-cursor sweep may treat as controls. `UNREACHED_JS`
#: uses the same list, because an element the two disagreed about would be
#: missing from the plan and from the count of what the plan missed.
CLICKY = 'div,span,li,td,th,section,p'

#: Cursors that mean an element is dragged rather than clicked, like a split
#: pane's `col-resize` bar or a sortable row's `move`. Clicking these does
#: nothing, so the surface drives them as handles.
DRAGGY =('col-resize', 'row-resize', 'ew-resize', 'ns-resize', 'nwse-resize',
          'nesw-resize', 'move', 'grab', 'grabbing', 'all-scroll')

#: Whether a label stands in for a radio or checkbox the page has hidden.
#: The element sweep and `UNREACHED_JS` share it, so the plan and the
#: unreached count agree about what was reached.
STANDS_IN_JS = """(l) => {
        const c = l.control;
        if (!c || c.tagName !== 'INPUT'
            || (c.type !== 'radio' && c.type !== 'checkbox')) return false;
        const cs = getComputedStyle(c), r = c.getBoundingClientRect();
        const lr = l.getBoundingClientRect();
        return (cs.display === 'none' || cs.visibility === 'hidden'
                || cs.opacity === '0' || r.width < 2 || r.height < 2)
            && lr.width > 2 && lr.height > 2;
    }"""

#: Reads a canvas's pixels, whatever its context type. The signature and the
#: element sweep share it, so they agree about what a canvas holds.
#:
#: A canvas keeps one context type for its life, so a WebGL canvas returns
#: `null` for a `2d` context. Those are read through `toDataURL` inside
#: `requestAnimationFrame`, because outside a frame the drawing buffer has
#: already been cleared and the image comes back blank. The image is drawn
#: onto a 2d canvas and measured the same way as any other.
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
              // The ink's colour range. A range of zero with every pixel
              // covered is a canvas filled with one colour, which `flat`
              // reports. Coverage is needed too, because a black line on a
              // transparent canvas is also one colour.
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
    // A selector matching only this element, built from the nearest ancestor
    // id and an nth-child path down from it. Without it, two inputs with no
    // id would both be `input`.
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
    // A widget is the smallest ancestor holding both a field and a button.
    // Controls in the same widget belong together, so three "New card" boxes
    // beside three "+" buttons make three widgets.
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
    const picked = new Set(document.querySelectorAll(__PICK__));
    // Editable regions and drag handles, which no tag marks as controls.
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
    // Elements with a pointer cursor count as controls. A grid of divs gets
    // its click handler from JavaScript, and listeners can't be read from the
    // DOM, so the cursor is the only sign the cells are clickable. Only the
    // innermost counts, so a pointer container around clickable cells isn't
    // a control of its own.
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
    // A label is the control when the page has hidden the radio or checkbox
    // it names. A star rating is often five labels over five radios set to
    // `display: none`, and the labels are what a person clicks.
    const standsIn = __PROXY__;
    const proxies = Array.from(document.querySelectorAll('label'))
        .filter(l => !picked.has(l) && standsIn(l));
    const out = Array.from(picked).concat(editable).concat(handles)
        .concat(cells).concat(proxies).slice(0, 250).map(el => {
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
            // Date and time inputs reject any text not in their format, so
            // they're a separate kind from text boxes.
            const dated = ['date', 'time', 'datetime-local', 'month', 'week'];
            o.kind = (t === 'checkbox' || t === 'radio' || t === 'range'
                      || t === 'number' || t === 'file' || t === 'color')
                     ? t : dated.includes(t) ? 'date' : 'text';
            o.type = t;
        } else if (o.tag === 'a' && el.getAttribute('href')) {
            o.kind = 'link';
        } else if (o.tag === 'canvas') { o.kind = 'canvas';
        // An element the page made editable, like a contentEditable
        // spreadsheet cell, is a text box without the tag.
        } else if (el.isContentEditable) { o.kind = 'text';
        // A handle is dragged, because clicking a split pane's bar or a
        // draggable row does nothing.
        } else if (handles.includes(el)) {
            o.kind = 'handle';
            o.grabbed = el.getAttribute('draggable') === 'true';
        } else if (cells.includes(el)) { o.kind = 'cell';
        } else if (proxies.includes(el)) { o.kind = el.control.type; }
        if (o.kind) {
            // A label's own words are its direct text nodes. Its nested
            // elements hold other things, like the options of a wrapped
            // select or a slider's live value, which would otherwise end up
            // in the control's name.
            const own = node => Array.from(node.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent).join(' ')
                .replace(/\\s+/g, ' ').replace(/[:\\s]+$/, '').trim();
            const labelEl = el.labels && el.labels[0] ? el.labels[0] : null;
            const lab = labelEl
                ? (own(labelEl) || (labelEl.innerText || '').trim()) : '';
            // A select's text is its options, which aren't its name.
            const self = o.tag === 'select' ? '' : (el.innerText || '').trim();
            o.label = (el.getAttribute('aria-label') || lab || self
                       || el.getAttribute('placeholder')
                       || el.getAttribute('title')
                       || el.getAttribute('value')
                       || el.id || '')
                .replace(/\\s+/g, ' ').trim().slice(0, 60);
            o.enabled = !el.disabled && !el.hasAttribute('aria-disabled');
            // The radio group, so a form can be filled by picking one from
            // each group.
            const box = proxies.includes(el) ? el.control : el;
            if (box.type === 'radio') o.radio = box.name || '';
            if (proxies.includes(el)) o.enabled = !box.disabled;
        }
        if (o.tag === 'img') {
            o.loaded = el.complete && el.naturalWidth > 0;
            o.src = el.getAttribute('src') || '';
        }
        if (o.tag === 'canvas') pending.push(
            _pixels(el).then(p => { o.painted = p[0]; }));
        if (o.kind) o.group = groupOf(el);
        // The tags and classes from this element up to the nearest ancestor
        // with an id. The element's own id is left out, so all the chips in
        // one tag bar share this value and a chip in another bar doesn't.
        if (o.kind) {
            const bits = [];
            for (let at = el; at && at !== document.body;
                 at = at.parentElement) {
                if (at !== el && at.id) { bits.unshift('#' + at.id); break; }
                const cls = Array.from(at.classList).sort().join('.');
                bits.unshift(at.tagName.toLowerCase() + (cls ? '.' + cls : ''));
            }
            o.family = bits.join(' > ');
        }
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
     .replace("__DRAGGY__", repr(list(DRAGGY))).replace("__CANVAS__", CANVAS_JS) \
     .replace("__PROXY__", STANDS_IN_JS)

#: What the page is showing, as a few values compared before and after an
#: action. Each one catches a change the others miss:
#:
#: * The painted count and centroid show whether something on a canvas moved.
#: * The mean colour catches an opaque cell repainted in another colour,
#:   which leaves the count, centroid, text and element count the same.
#: * An exact pixel hash catches a single brush stroke, which barely moves
#:   the rounded mean on a large canvas.
#: * The field values catch a result written into an input.
#: * A hash of every element's style and class catches a DOM grid that
#:   paints a cell by setting its `style`.
SIGNATURE_JS = """async () => {
__CANVAS__    return {
    canvas: await Promise.all(
        Array.from(document.querySelectorAll('canvas')).map(_pixels)),
    text: (document.body.innerText || '').slice(0, 400),
    // Field values aren't in `innerText`, the styles or a canvas, so a page
    // whose result lands in an input, like a unit converter, would look
    // unchanged without this.
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


#: What the page offers, as a hash plus counts of its controls and content.
#:
#: The hash covers the element count and each control's tag, label, size and
#: state. It leaves out the page's other text and its pixels, because a clock
#: or an animation changes those all the time on a working page. A page
#: showing only a loading spinner has an unchanging hash too, so `settle` also
#: waits for `live`, the count of working controls.
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
    // The pointer-cursor cells go into the hash too, because the plan is
    // built from them as well as `PICK`, and a board isn't ready while its
    // cells are still being added. Only their count goes in, because a
    // cell's text changes during play and would stop the page settling.
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
            // A canvas isn't a named control. An empty canvas may be all a
            // dead page has, so counting it here would excuse that page.
            if (el.tagName !== 'CANVAS') named++;
        }
    // The surface treats an editable region as a text box, so it counts as a
    // control here. Otherwise a sheet of contentEditable cells would have
    // nothing to work and every open would wait for the ceiling.
    for (const el of document.querySelectorAll('[contenteditable]'))
        if (el.getAttribute('contenteditable') !== 'false' && working(el)) {
            live++;
            named++;
        }
    // A pointer cursor marks something to click. A grid is often plain divs
    // with one handler on their parent, which can't be read from here, but
    // the cursor can. A grab or resize cursor, or `draggable`, marks a
    // handle, which the surface drags, so those count too.
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

    // Whether a person would see anything at all, which `live` doesn't
    // measure. A page of only prose has no controls and isn't blank.
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
        } catch (e) { shown += 1; }   // unreadable isn't empty
    }
    // `live` includes the pointer cells, because `settle` waits for `live`
    // and has to count what the surface counts as a control. Counting only
    // form controls made a board of clickable divs wait for the ceiling on
    // every open.
    return {h: h, live: live + pointing, named: named + pointing,
            shown: shown};
}""".replace("__PICK__", repr(PICK)).replace("__CLICKY__", repr(CLICKY)) \
     .replace("__DRAGGY__", repr(list(DRAGGY)))


class Settled(NamedTuple):
    """How a page came to rest.

    A page still changing, a page that stopped with nothing to work, and a
    page that rendered nothing are kept apart, because only the last is a
    fault on its own.
    """

    #: Whether the structure stopped changing.
    quiet: bool
    #: Working controls on the page at the end. With none, `settle` watches
    #: until the ceiling instead of stopping when the page goes quiet.
    live: int
    #: `live` without canvases. A page whose only control is an empty canvas
    #: is dead, and `live` alone would count it as having something to work.
    named: int
    #: How much the page rendered, counting text, loaded images and painted
    #: canvases. Zero is a blank page, but only when `measured` is true.
    shown: int
    #: How long `settle` watched, in milliseconds.
    ms: int
    #: Whether any reading came back. A page that overwrites a global the
    #: driver evaluates through, like a calculator that declares a function
    #: named `eval`, returns nothing for every reading while still working,
    #: and mustn't be reported as blank.
    measured: bool = True


def settle(page: Any, poll_ms: int = 100, stable: int = 3,
           ceiling_ms: int = 15000) -> "Settled":
    """Wait until the page's controls stop changing, and say how it ended.

    The page counts as ready after `stable` polls with the same structure
    hash, but only once it offers something to work. A page showing only a
    loading message is unchanging too, so an empty page is watched until the
    ceiling. A fixed pause would measure a slow framework before it mounts.

    Reaching the ceiling is reported in the result, not treated as a fault.
    A growing feed or a carousel never settles, and the page as it stands at
    the ceiling is still the best measurement. Whether an empty page is a
    fault is for the caller to decide.
    """
    seen: Any = None
    same, waited = 0, 0
    read_one = False
    while waited < ceiling_ms:
        try:
            now = page.evaluate(STRUCTURE_JS)
        except Exception:
            # The page is navigating or has closed. Try again next poll.
            now = None
        # Track whether any reading came back, so a page that blocks
        # readings isn't reported the same way as an empty one.
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
    """Draw a stroke across an element with the mouse held down.

    A freehand canvas responds only to press, move and release. The target
    may carry `@x,y` to say where the stroke starts, so a second stroke can
    cover different pixels from the first. A stroke over pixels that are
    already that colour changes nothing, and a working painter would look
    broken.
    """
    sel, _, spot = target.partition("@")
    box = page.query_selector(sel).bounding_box()
    x, y = box["x"], box["y"]
    w, h = box["width"], box["height"]
    try:
        fx, fy = (float(n) for n in spot.split(","))
    except ValueError:
        fx = fy = CANVAS_X
    # Step away from the nearest edges so the stroke stays inside the box. A
    # stroke that ends outside releases the mouse on the page instead of the
    # canvas, and a painter that commits on `mouseup` draws nothing.
    dx, dy = (-0.09 if fx > 0.5 else 0.09), (-0.07 if fy > 0.5 else 0.07)
    page.mouse.move(x + w * fx, y + h * fy)
    page.mouse.down()
    for step in range(1, 7):
        page.mouse.move(x + w * (fx + step * dx), y + h * (fy + step * dy))
        page.wait_for_timeout(40)
    page.mouse.up()
    page.wait_for_timeout(150)


def answer_dialogs(page: Any) -> None:
    """Accept every dialog the page opens, and record its alerts.

    A driver dismisses `prompt`, `confirm` and `alert` by default, which
    answers no to everything. A kanban board that asks for a card's title
    through a `prompt` then correctly adds nothing. Accepting is what a
    person trying the feature does. A `prompt` gets the value a text field
    with the same words would get, so "How many?" gets a number.
    """
    heard = _DIALOGS.setdefault(page, [])

    def answer(dialog: Any) -> None:
        with contextlib.suppress(Exception):
            # Only an alert counts as the page responding. A prompt or a
            # confirm is a question, and the response is whatever the page
            # does with the answer.
            if dialog.type == "alert":
                heard.append(str(dialog.message or "")[:120])
            if dialog.type == "prompt":
                dialog.accept(sample_for(dialog.message))
            else:
                dialog.accept()
    page.on("dialog", answer)


#: The alerts each open page has raised, in order. An alert like "Length
#: must be mm:ss" is the page responding, and leaves nothing in the document
#: to measure.
_DIALOGS: "weakref.WeakKeyDictionary[Any, List[str]]" = weakref.WeakKeyDictionary()


def sample_for(words: str) -> str:
    """A plausible value for a prompt or field, from the words asking for it.

    The plan's `_typed_for` uses this too, so a `prompt` and a field that ask
    for the same thing get the same value.
    """
    name = (words or "").lower()
    if "mail" in name:
        return "someone@example.com"
    # Phone and time fields often check their format, so a sentence fails.
    if any(word in name for word in ("phone", "tel", "mobile")):
        return "555-0100"
    if "mm:ss" in name or "duration" in name:
        return "3:30"
    if "hh:mm" in name:
        return "09:30"
    # Address fields often check the value with `new URL(...)`, which
    # rejects `Sample item`.
    if any(word in name for word in ("url", "link", "http", "website",
                                     "web address", "site")):
        return "https://example.com/page"
    if any(word in name for word in
           ("number", "digit", "amount", "price", "qty", "quantity",
            "age", "year", "second", "minute", "value", "how many")):
        return "5"
    return "Sample item"


#: Boxes whose own placeholder fails their own `pattern`, which usually means
#: no value can pass.
#:
#: For example, `pattern="\\d{5}"` written with an escaped backslash matches a
#: literal backslash followed by five d's, so no postcode passes and the form
#: step can never be completed. Driving the page can't find this when the
#: field is on a later, hidden step, so the pattern is checked directly.
#:
#: The check runs on a detached copy, so the real input is never written to,
#: and uses the browser's own validator. A placeholder containing a space is
#: skipped, because it's usually an instruction rather than an example value.
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
    """Boxes whose own placeholder fails their `pattern`. See `UNFILLABLE_JS`."""
    try:
        got = page.evaluate(UNFILLABLE_JS)
        return got if isinstance(got, list) else []
    except Exception:
        return []


def rendered(page: Any) -> Optional[Dict[str, int]]:
    """How much the page shows and how many controls it has right now.

    One reading of the measurement `settle` watches. `None` means the reading
    failed, which isn't the same as an empty page.
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
    """Whether the canvases stopped changing, and whether they changed first.

    A canvas that's quiet and never moved is a still picture. One that went
    quiet after moving is a program that ran and reached a state of its own,
    and what it does next says nothing about whether it was wired up.
    """

    quiet: bool
    #: Whether the canvases changed at any point during the watch.
    moved: bool


def settle_canvas(page: Any, poll_ms: int = 200, stable: int = 3,
                  ceiling_ms: int = 4000) -> Rested:
    """Wait for the canvases to stop changing on their own.

    A canvas check compares the page before and after a gesture, and a game
    that animates by itself changes in that window whether or not anything
    was pressed. So the canvas is brought to rest first. If it's still
    changing at the ceiling, the caller doesn't attribute any change to the
    gesture.
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


#: Counts of elements that look interactive but aren't in the plan, keyed by
#: the reason they look interactive.
#:
#: The finding that nothing on a page responds is drawn from the plan, so
#: it's only fair when the plan reached everything. On a sortable table, a
#: plan that reached only the data cells misses the headers that do the
#: sorting. A changed cursor, `contenteditable` and `draggable` each show the
#: plan missed something, without needing to read a listener.
#:
#: This counts what's left over, not what was found, so a small page whose
#: plan is complete reports nothing.
UNREACHED_JS = """() => {
    const seen = (el) => { const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return r.width > 6 && r.height > 6 && cs.display !== 'none'
            && cs.visibility !== 'hidden' && cs.opacity !== '0'; };
    // What the plan is built from, selected the same way as `ELEMENTS_JS`.
    const reached = new Set(document.querySelectorAll(__PICK__));
    const standsIn = __PROXY__;
    for (const l of document.querySelectorAll('label'))
        if (standsIn(l)) reached.add(l);
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
    // Any cursor the page set, other than these, marks something to use.
    // `text` is a caret over prose, and `not-allowed`, `wait` and `progress`
    // are refusals. A `pointer` element is counted only when the sweep above
    // didn't reach it.
    for (const el of document.querySelectorAll('*')) {
        const c = getComputedStyle(el).cursor;
        if (['auto', 'default', 'text', 'none', 'not-allowed', 'wait',
             'progress', 'help', 'inherit'].includes(c)) continue;
        note(el, c);
    }
    return out;
}""".replace("__PICK__", repr(PICK)).replace("__CLICKY__", repr(CLICKY)) \
     .replace("__GRABBY__", repr(list(DRAGGY))) \
     .replace("__PROXY__", STANDS_IN_JS)


def unreached(page: Any) -> Dict[str, int]:
    """Interactive-looking elements the plan doesn't include, by reason.

    Empty means the plan covers everything the page marks as usable, which
    is when a page-wide finding is fair.
    """
    try:
        return dict(page.evaluate(UNREACHED_JS))
    except Exception:
        # A failed read returns empty rather than failing the run.
        return {}


def elements(page: Any) -> List[Element]:
    """Every control the page rendered, read from the live page.

    Reading the rendered page instead of the markup includes controls built
    at run time, and records whether the CSS hides each one.
    """
    try:
        rows = page.evaluate(ELEMENTS_JS)
    except Exception:
        return []
    # A page that replaced a global the driver evaluates through can return
    # anything, so only a list of dicts counts as a reading.
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
            input_type=str(r.get("type") or ""),
            radio=str(r.get("radio") or ""),
            family=str(r.get("family") or ""),
            painted=r.get("painted"), loaded=r.get("loaded"),
            src=str(r.get("src") or "")[:200],
        )
        for r in rows or []
    ]


#: Mistakes a page shows about itself whatever it's for, read in one round
#: trip after a case acts.
#:
#: `computed` lists text only a bug produces. `[object Object]` is an object
#: printed where one of its fields was meant, `NaN` is arithmetic on
#: something that isn't a number, and `undefined` is a variable read before
#: it was set. `null` is left out, because a table can legitimately show a
#: database null.
#:
#: `wiring` lists three markup mistakes. Two radios in one group share a
#: value, so the form can't tell them apart. Two labels point at one control,
#: which leaves another control unlabelled. A label points at an id that
#: doesn't exist.
#:
#: `aria` lists controls marked as showing a panel that isn't shown.
#:
#: There's deliberately no check for a page saying it's empty while it shows
#: items. A cart's "Your basket is empty" sits beside the catalogue, and
#: nothing mechanical can tell which list a sentence is about.
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
                wiring.push('two radio buttons in the "' + name + '" group '
                    + 'both have the value "' + el.value + '", so the form '
                    + 'can\'t tell which of them was picked');
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
            wiring.push('the label "' + words + '" is linked to "' + at
                + '", but nothing on the page has that id');
        } else if (pointed[at]) {
            wiring.push('two labels are both linked to "' + at + '", so '
                + 'one of them was meant for another control, which is left '
                + 'without a label');
        }
        pointed[at] = 1;
    }

    // A tab with aria-selected="true" or a header with aria-expanded="true"
    // names the panel it shows in aria-controls. When that panel isn't
    // rendered, the markup contradicts what's on screen. An empty panel
    // still has a box, so only a panel the browser doesn't render counts.
    const aria = [];
    const rendered = (el) => el.getClientRects().length > 0
        && getComputedStyle(el).visibility !== 'hidden';
    for (const el of document.querySelectorAll(
             '[aria-controls][aria-selected=true], '
             + '[aria-controls][aria-expanded=true]')) {
        if (!rendered(el)) continue;
        const says = el.getAttribute('aria-selected') === 'true'
            ? 'selected' : 'expanded';
        for (const id of (el.getAttribute('aria-controls') || '').split(/\s+/)) {
            const target = id && document.getElementById(id);
            if (target && !rendered(target)) {
                aria.push('"' + (el.innerText || '').trim().slice(0, 24)
                    + '" is marked ' + says + ' and controls the panel "' + id
                    + '", but that panel isn\'t shown');
            }
        }
    }

    return {computed: computed, wiring: wiring, aria: aria};
}"""


#: How many items of each kind are on show, and every number the page
#: displays on its own. The run compares these across actions, and a number
#: that moves one for one with a list is counting it.
#:
#: A number is a leaf element holding only a number. An element with children
#: is a container whose text belongs to them. A number with a decimal point
#: is reported but never treated as a count, so a price isn't mistaken for
#: one.
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

    // One reading can't tell which classes are lists, because a list holding
    // one row looks like any other element. So every class is reported with
    // how many are on show, and the run decides which are lists once it has
    // seen them at more than one size.
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
        // A count needs a whole number, so a price isn't read as one. A
        // number that follows the list only needs to move, so a running
        // total with decimals is still reported.
        const whole = /^-?\d{1,6}$/.test(said);
        const anyNum = /^-?\d{1,9}(\.\d{1,4})?$/.test(said);
        if (!anyNum) continue;
        numbers.push({at: where(el), is: whole ? parseInt(said, 10) : null,
                      said: said});
    }
    return {rows: rows, classes: classes, numbers: numbers,
            texts: texts, rowText: rowText.slice(0, 600)};
}"""


#: The row a control sits in, and the rows like it. A row is the first
#: ancestor with at least one sibling of the same tag and class.
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

#: The same rows, found from their container's path instead of from the
#: control. Once a row is removed, walking up from the control may miss the
#: list, because with one row left it has no siblings to match, and the walk
#: reaches a larger grouping further out, so the count appears to go up.
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
    """The rows in that container now, found without the control."""
    if not holder:
        return None
    try:
        got = page.evaluate(ROWS_JS, [holder, shape])
        return got if isinstance(got, dict) else None
    except Exception:
        return None


def row_of(page: Any, selector: str) -> Optional[Dict[str, Any]]:
    """Which row this control is in, and the text of every row like it."""
    if not selector:
        return None
    try:
        got = page.evaluate(ROW_JS, selector)
        return got if isinstance(got, dict) else None
    except Exception:
        return None


def counted(page: Any) -> Dict[str, Any]:
    """How many items are on show, and the numbers the page displays."""
    try:
        got = page.evaluate(COUNTED_JS)
        return got if isinstance(got, dict) else {}
    except Exception:
        return {}


#: Which typed strings appear nowhere a reader could find them, meaning the
#: visible text, the boxes' values, and attributes like `href` and `title`.
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


#: Everything the page has put in its own storage, as one string.
_STORED_JS = """() => {
    const dump = (s) => {
        try { return JSON.stringify(Object.assign({}, s)); }
        catch (e) { return ''; }
    };
    return dump(window.localStorage) + ' ' + dump(window.sessionStorage);
}"""


def saved(page: Any, typed: Sequence[str]) -> List[str]:
    """Which of these the page both stored and is showing right now."""
    if not typed:
        return []
    try:
        stored = str(page.evaluate(_STORED_JS) or "")
    except Exception:
        return []
    kept = [one for one in typed if one in stored]
    shown = set(kept) - set(missing_from(page, kept))
    return [one for one in kept if one in shown]


# There's deliberately no check that a box keeps exactly what was typed into
# it. A quantity box with a maximum of ten correctly holds ten when given
# twenty-five, and a stepper restores its minimum when it's emptied.
def missing_from(page: Any, needles: Sequence[str]) -> List[str]:
    """Which of these the page isn't showing anywhere."""
    if not needles:
        return []
    try:
        return list(page.evaluate(SHOWS_JS, list(needles)) or [])
    except Exception:
        return []


def facts(page: Any) -> Dict[str, Any]:
    """Mistakes the page shows about itself. See `FACTS_JS`."""
    try:
        got = page.evaluate(FACTS_JS)
        return got if isinstance(got, dict) else {}
    except Exception:
        return {}


def signature(page: Any) -> Dict[str, Any]:
    """What the page is showing, for comparing before and after an act.

    It includes how many alerts the page has raised and the last one's text,
    because a page that rejects bad input with an `alert` changes nothing in
    the document.
    """
    try:
        got = page.evaluate(SIGNATURE_JS)
    except Exception:
        return {}
    if isinstance(got, dict):
        heard = _DIALOGS.get(page) or []
        got["dialogs"] = len(heard)
        got["dialog"] = heard[-1] if heard else ""
    return got


# --------------------------------------------------------------------------
# Acting
# --------------------------------------------------------------------------

#: jQuery's `:contains()`, which models often write and no browser supports.
#: `perform` rewrites it to Playwright's `:has-text()`, which means the same.
_CONTAINS = re.compile(r":contains\(([^)]*)\)")


def _where(page: Any, selector: str, spot: str = "") -> Dict[str, Any]:
    """Where inside an element to click.

    A canvas is clicked off-centre (see `CANVAS_X`). `spot` overrides that
    with an `x,y` fraction of the box, so a plan can click one canvas at
    several different points.
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
        # Fall back to the default click point rather than fail the click.
        return {}


def _found(page: Any, selector: str) -> bool:
    """Whether the selector matches an element on the page."""
    try:
        return page.query_selector(selector) is not None
    except Exception:
        return False


def _disabled(page: Any, selector: str) -> bool:
    """Whether the page has that control disabled.

    Playwright times out on a disabled control the same way as on a missing
    one, and a correctly disabled control, like Undo with nothing to undo,
    isn't a defect.
    """
    try:
        el = page.query_selector(selector)
        return bool(el) and bool(
            el.get_attribute("disabled") is not None
            or el.get_attribute("aria-disabled"))
    except Exception:
        return False


#: The end of a slider's range farther from its current value, so moving it
#: there always changes the value.
_REACH_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const lo = Number(el.min === '' ? 0 : el.min);
    const hi = Number(el.max === '' ? 100 : el.max);
    const now = Number(el.value);
    return String(now - lo > hi - now ? lo : hi);
}"""


def _slide(page: Any, selector: str, timeout: float) -> None:
    """Move a slider to whichever end of its range is farther away.

    A fixed value might be where the slider already sits, and then nothing
    changes. The value is filled instead of dragged, because a drag lands
    wherever the pixels fall and two runs could disagree.
    """
    reach = page.evaluate(_REACH_JS, selector)
    if reach is None:
        raise ValueError(f"no element matches {selector}")
    page.fill(selector, reach, timeout=timeout)


#: The index of the next enabled option after the selected one, wrapping
#: round. Disabled options, like a "Choose..." placeholder, are skipped.
_OTHER_OPTION_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el || !el.options || !el.options.length) return null;
    const at = el.selectedIndex;
    for (let i = 1; i <= el.options.length; i++) {
        const k = (at + i + el.options.length) % el.options.length;
        if (k !== at && !el.options[k].disabled) return k;
    }
    return null;
}"""


def _choose(page: Any, selector: str, timeout: float) -> None:
    """Pick a different option in a select, the way a person does.

    Clicking a select only opens it, so its `change` handler never runs.
    Selecting an option fires it.
    """
    at = page.evaluate(_OTHER_OPTION_JS, selector)
    if at is None:
        raise ValueError(f"{selector} has no other option to choose")
    page.select_option(selector, index=at, timeout=timeout)


def _recolour(page: Any, selector: str, timeout: float) -> None:
    """Set a colour box to a colour it isn't already showing."""
    now = page.evaluate("(s) => { const e = document.querySelector(s); "
                        "return e ? String(e.value).toLowerCase() : null; }",
                        selector)
    if now is None:
        raise ValueError(f"no element matches {selector}")
    page.fill(selector, "#cc6633" if now == "#3366cc" else "#3366cc",
              timeout=timeout)


#: A one-pixel PNG, so a page that previews an uploaded image has something
#: to show.
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQ"
    "GAhKmMIQAAAABJRU5ErkJggg==")


def _attach(page: Any, selector: str, timeout: float) -> None:
    """Give a file box a small file of the kind it says it accepts."""
    accept = (page.get_attribute(selector, "accept", timeout=timeout)
              or "").lower()
    if "image" in accept or any(x in accept for x in
                                (".png", ".jpg", ".jpeg", ".gif", ".webp")):
        one = {"name": "sample.png", "mimeType": "image/png", "buffer": _PNG}
    elif "json" in accept:
        one = {"name": "sample.json", "mimeType": "application/json",
               "buffer": b'{"name": "Sample item", "value": 5}\n'}
    elif "csv" in accept:
        one = {"name": "sample.csv", "mimeType": "text/csv",
               "buffer": b"name,value\nSample item,5\n"}
    else:
        one = {"name": "sample.txt", "mimeType": "text/plain",
               "buffer": b"Sample item\n"}
    page.set_input_files(selector, files=[one], timeout=timeout)


def perform(page: Any, acts: Sequence[Dict[str, str]],
            timeout: float = 4000) -> Tuple[List[str], List[str]]:
    """Do each act in order.

    Returns the acts that failed, and the clicks that hit a disabled
    control. A target may carry `@x,y` to name a point as a fraction of the
    element's box. A click tries the target as a selector and then as the
    words on the control, so `{"click": "Start"}` works.
    """
    could_not: List[str] = []
    was_off: List[str] = []
    for step in acts:
        for verb, raw in step.items():
            arg = _CONTAINS.sub(r":has-text(\1)", str(raw))
            try:
                if verb in ("click", "dblclick", "pick"):
                    sel, _, spot = arg.partition("@")
                    try:
                        page.click(sel, timeout=timeout, **_where(page, sel, spot))
                    except Exception:
                        # Try the words only when the selector matched
                        # nothing. A matched element that couldn't be clicked
                        # won't match as text either, and trying costs a
                        # second full timeout.
                        if _found(page, sel):
                            raise
                        page.click(f"text={sel}", timeout=timeout)
                elif verb == "press":
                    page.keyboard.press(arg)
                elif verb in ("fill", "enter"):
                    sel, _, value = arg.partition("=")
                    page.fill(sel.strip(), value.strip(), timeout=timeout)
                    if verb == "enter":
                        # Blur the box, because `change` only fires when it
                        # loses focus. The plan uses `enter` when typing is
                        # a case's last act. Otherwise the next press moves
                        # the focus.
                        page.eval_on_selector(sel.strip(), "e => e.blur()")
                elif verb == "choose":
                    _choose(page, arg, timeout)
                elif verb == "recolour":
                    _recolour(page, arg, timeout)
                elif verb == "attach":
                    _attach(page, arg, timeout)
                elif verb == "drag":
                    _drag(page, arg)
                elif verb == "slide":
                    _slide(page, arg, timeout)
                elif verb == "dragonto":
                    # A `draggable` element moves through HTML5 drag events,
                    # which a mouse press, move and release don't send.
                    # Playwright's `drag_and_drop` sends them.
                    src, _, dst = arg.partition(">>")
                    page.drag_and_drop(src.strip(), dst.strip(),
                                       timeout=timeout)
                elif verb == "reload":
                    page.reload(wait_until="load", timeout=30000)
                    settle(page, ceiling_ms=5000)
                elif verb == "wait":
                    page.wait_for_timeout(min(int(float(arg) * 1000), 10000))
                else:
                    continue
            except Exception as exc:
                target = str(raw).split("@")[0]
                if verb in ("click", "dblclick", "pick") \
                        and _disabled(page, target):
                    was_off.append(f"{verb} {raw}")
                else:
                    could_not.append(
                        f"{verb} {raw}: {str(exc).splitlines()[0][:120]}")
    if acts:
        with contextlib.suppress(Exception):
            # Move the pointer to the corner before measuring. A canvas that
            # draws a hover highlight repaints wherever the mouse was left,
            # which would look like a response to the click.
            page.mouse.move(1, 1)
            page.wait_for_timeout(500)
    return could_not, was_off


# --------------------------------------------------------------------------
# Comparing
# --------------------------------------------------------------------------

def changed(was: Dict[str, Any], now: Dict[str, Any]) -> str:
    """What changed between two signatures, in numbers a reader can check.

    It's reported whether the case passed or failed, because only a reader
    can judge the direction of a change. For example, a centre moving from
    (640, 320) to (640, 704) after pressing Left shows the piece fell but
    didn't move sideways.
    """
    if not was or not now:
        return ""
    bits: List[str] = []
    for i, (a, b) in enumerate(zip(was.get("canvas") or [], now.get("canvas") or [])):
        if a == b:
            bits.append(f"canvas {i} unchanged ({a[0]} painted px)")
        elif len(a) > 6 and len(b) > 6 and a[:6] == b[:6]:
            bits.append(f"canvas {i} changed, but its painted pixel count, "
                        f"centre and mean colour stayed the same ({a[0]} "
                        f"painted px)")
        else:
            said = (f"canvas {i} went from {a[0]} to {b[0]} painted px, "
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
        bits.append("the values in the fields changed")
    if was.get("styles") != now.get("styles"):
        bits.append("something on the page was restyled or recoloured")
    if int(now.get("dialogs") or 0) > int(was.get("dialogs") or 0):
        bits.append(f"the page showed an alert, {now.get('dialog')!r}")
    return ", ".join(bits)


def moved(was: Dict[str, Any], now: Dict[str, Any]) -> Optional[bool]:
    """Whether the page was measurably different afterwards.

    `None` when either reading is missing. That must never count as no
    change, or a working page fails on a measurement that never happened.
    """
    if not was or not now:
        return None
    return was != now


def canvas_still(was: Dict[str, Any], now: Dict[str, Any]) -> bool:
    """Whether every canvas's exact pixel hash is unchanged afterwards.

    `moved` compares the whole signature, whose rounded canvas values can
    miss a single brush stroke. This compares only the exact hash, because
    the question is whether the canvas changed at all.
    """
    before, after = (was or {}).get("canvas"), (now or {}).get("canvas")
    if not before or not after or len(before) != len(after):
        return False

    def stamp(rows: Sequence[Any]) -> List[Any]:
        return [r[6] if isinstance(r, list) and len(r) > 6 else r for r in rows]

    return stamp(before) == stamp(after)


def unpainted(now: Dict[str, Any]) -> int:
    """How many canvases have nothing drawn in them.

    A canvas counts as empty when nothing is painted, or when one colour
    covers every pixel. The second case catches a WebGL canvas, which starts
    filled with its clear colour, so every pixel counts as painted. Full
    coverage is required, because on a 2d canvas only the ink is counted and
    a single black line is also one colour. A canvas that couldn't be read
    reports `-1` and isn't counted as empty.
    """
    return sum(1 for row in (now or {}).get("canvas") or []
               if isinstance(row, list) and row
               and (row[0] == 0 or (len(row) > 7 and row[7] == 1)))


#: A key the page's visible text says to press.
_TOLD = re.compile(r"\b(?:press|hit|tap)\s+(?:the\s+)?"
                   r"(space\s?bar|space|enter|return|escape|esc|any\s+key)\b",
                   re.I)

_NAMED_KEY = {"space": "Space", "spacebar": "Space", "space bar": "Space",
              "enter": "Enter", "return": "Enter",
              "escape": "Escape", "esc": "Escape"}


def told_to_press(text: str) -> str:
    """The key the page asks for, `*` for any key, or empty for none.

    A game that shows "Press Space to restart" and then ignores Space is
    stuck, while one that asks for nothing and ignores the keyboard may just
    be finished. `text` is the page's rendered text.
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


#: One element, in enough detail to tell whether it changed. Its markup
#: catches a class or its text changing, and its computed colours and
#: transform catch the page styling it directly.
#:
#: The class, style and transform of three ancestors are included too,
#: because a click often changes a wrapper. A flashcard flips by adding a
#: class to the card, and the face that was clicked stays the same. Three
#: levels cover the usual wrappers without counting changes elsewhere on the
#: page.
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
    """The element's markup and styling, or None if it isn't there."""
    if not selector:
        return None
    try:
        got = page.evaluate(ITSELF_JS, selector)
        return None if got is None else str(got)
    except Exception:
        return None


#: A hash of the page without one control, to show whether a press changed
#: anything elsewhere. It covers each element outside the control by its tag,
#: class, style, value and text. The control's subtree is left out, and so
#: are the class and style of the three ancestors `ITSELF_JS` reads.
OUTSIDE_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el || !document.body) return null;
    const near = new Set();
    for (let up = el.parentElement, n = 0; up && n < 3;
         up = up.parentElement, n++) near.add(up);
    let h = 0;
    const eat = (s) => {
        for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    };
    for (const node of document.body.querySelectorAll('*')) {
        if (el.contains(node)) continue;
        eat('<' + node.tagName);
        if (!near.has(node)) {
            eat((typeof node.className === 'string' ? node.className : '')
                + '|' + (node.getAttribute('style') || '')
                + '|' + (node.hidden ? 'hidden' : ''));
            if (/^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName))
                eat('=' + String(node.type === 'checkbox' || node.type === 'radio'
                                 ? node.checked : node.value));
        }
        for (const t of node.childNodes)
            if (t.nodeType === 3) eat(t.textContent);
    }
    return h;
}"""


def outside(page: Any, selector: str) -> Optional[int]:
    """A hash of the page apart from this control, or None if unreadable."""
    if not selector:
        return None
    try:
        got = page.evaluate(OUTSIDE_JS, selector)
        return got if isinstance(got, int) else None
    except Exception:
        return None


def aimed_at_canvas(acts: Sequence[Dict[str, str]]) -> bool:
    """Whether an act clicks a canvas.

    The page-wide check passes when anything on the page changes, so a grid
    that announces each click in a live region passes even when the clicked
    canvas stays the same. For an act aimed at a canvas, the caller checks
    the canvas itself.
    """
    for step in acts or ():
        for verb, arg in step.items():
            if verb in ("click", "dblclick") and "canvas" in str(arg).lower():
                return True
    return False
