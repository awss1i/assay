"""The HTML report.

For each case the report shows the page before and after, and the
measurement that decided the outcome, so a reader can check every verdict.
It's one HTML file with the screenshots in a folder beside it. It needs no CDN
or build step, so it opens straight from disk or a CI artifact, and it follows
the reader's light or dark theme.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

_CSS = """
:root {
  --bg: #fbfbfa; --fg: #1a1a19; --dim: #6b6b68; --line: #e3e3e0;
  --card: #ffffff; --ok: #157f3d; --bad: #b3261e; --unknown: #8a6d1f;
  --ok-bg: #eef7f0; --bad-bg: #fdf0ef; --unknown-bg: #fdf6e6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17181a; --fg: #e8e8e6; --dim: #9a9a96; --line: #2e2f32;
    --card: #1e1f22; --ok: #6cc48b; --bad: #f2857c; --unknown: #d9b75f;
    --ok-bg: #17251c; --bad-bg: #2a1a19; --unknown-bg: #26211440;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 60rem; margin: 0 auto; padding: 2.5rem 1.25rem 5rem; }
h1 { font-size: 1.5rem; margin: 0 0 .3rem; letter-spacing: -.01em; }
.sub { color: var(--dim); margin: 0 0 2rem; font-size: .95rem; }
.tally { display: flex; gap: .5rem; flex-wrap: wrap; margin: 0 0 2.5rem; }
.pill {
  border: 1px solid var(--line); border-radius: 999px;
  padding: .3rem .85rem; font-size: .85rem; font-variant-numeric: tabular-nums;
}
.pill b { font-weight: 600; }
.pill.ok { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 35%, var(--line)); }
.pill.bad { color: var(--bad); border-color: color-mix(in srgb, var(--bad) 35%, var(--line)); }
.case {
  border: 1px solid var(--line); border-radius: 10px; background: var(--card);
  margin: 0 0 1rem; overflow: hidden;
}
.case > summary {
  cursor: pointer; padding: .85rem 1rem; display: flex; gap: .7rem;
  align-items: baseline; list-style: none;
}
.case > summary::-webkit-details-marker { display: none; }
.case[open] > summary { border-bottom: 1px solid var(--line); }
.tag {
  font-size: .7rem; font-weight: 600; letter-spacing: .04em;
  text-transform: uppercase; padding: .18rem .5rem; border-radius: 5px;
  flex: none;
}
.tag.ok { color: var(--ok); background: var(--ok-bg); }
.tag.bad { color: var(--bad); background: var(--bad-bg); }
.tag.unknown { color: var(--unknown); background: var(--unknown-bg); }
.id { color: var(--dim); font: 500 .8rem ui-monospace, SFMono-Regular, Menlo, monospace; flex: none; }
.what { flex: 1; }
.body { padding: 1rem; }
.why {
  margin: 0 0 1rem; padding: .7rem .9rem; border-radius: 7px;
  background: var(--bad-bg); color: var(--bad); font-size: .9rem;
}
.measured {
  margin: 0 0 1rem; color: var(--dim); font-size: .85rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; word-break: break-word;
}
.acts { margin: 0 0 1rem; font-size: .85rem; color: var(--dim); }
.link { margin: -.5rem 0 1rem; font-size: .85rem; color: var(--unknown); }
.link a { color: inherit; }
.acts code {
  background: color-mix(in srgb, var(--fg) 7%, transparent);
  padding: .1rem .35rem; border-radius: 4px; margin-right: .3rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.shots { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: .75rem; }
.shot figcaption {
  font-size: .75rem; color: var(--dim); margin: 0 0 .35rem;
  text-transform: uppercase; letter-spacing: .05em;
}
.shot img {
  width: 100%; border: 1px solid var(--line); border-radius: 7px; display: block;
  background: #fff;
}
.surface { margin: 3rem 0 0; }
.surface h2 { font-size: 1rem; margin: 0 0 .75rem; }
.surface pre {
  border: 1px solid var(--line); border-radius: 10px; background: var(--card);
  padding: 1rem; overflow-x: auto; font-size: .82rem; margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
footer { margin: 3rem 0 0; color: var(--dim); font-size: .8rem; }
footer a { color: inherit; }
"""


def _case_html(result: Any, shots_dir: str) -> str:
    """One case as a `<details>` block, open when it failed."""
    from assay.qa import FAILED, PASSED

    kind = {PASSED: "ok", FAILED: "bad"}.get(result.outcome, "unknown")
    word = {PASSED: "pass", FAILED: "fail"}.get(result.outcome, "not checked")
    case = result.case

    acts = "".join(
        f"<code>{html.escape(f'{verb} {arg}')}</code>"
        for step in case.acts for verb, arg in step.items())

    shots = "".join(
        f'<figure class="shot"><figcaption>{html.escape(when)}</figcaption>'
        f'<img loading="lazy" src="{html.escape(shots_dir)}/{html.escape(name)}"'
        f' alt="the page {html.escape(when)} {html.escape(case.what)}"></figure>'
        for when, name in result.artifacts.items() if name)

    # Turn the first mention of the linked case's id into an anchor to it.
    notes = "".join(
        '<p class="link">↳ ' + html.escape(one.why).replace(
            html.escape(one.to),
            f'<a href="#{html.escape(one.to)}">{html.escape(one.to)}</a>', 1)
        + "</p>"
        for one in getattr(result, "links", []))

    return (
        f'<details class="case" id="{html.escape(case.id)}"'
        f'{" open" if result.failed else ""}>'
        f'<summary><span class="tag {kind}">{word}</span>'
        f'<span class="id">{html.escape(case.id)}</span>'
        f'<span class="what">{html.escape(case.what)}</span></summary>'
        f'<div class="body">'
        + (f'<p class="why">{html.escape(result.detail)}</p>' if result.detail else "")
        + notes
        + (f'<p class="acts">{acts}</p>' if acts else
           '<p class="acts">assay opened the page and did nothing else</p>')
        + (f'<p class="measured">{html.escape(result.evidence)}</p>'
           if result.evidence else "")
        + (f'<div class="shots">{shots}</div>' if shots else "")
        + "</div></details>")


def write(run: Any, where: str | Path, folder: str = "",
          shots_dir: str = "shots") -> Path:
    """Write the report to `where` and return its path."""
    from assay.qa import PASSED

    out = Path(where).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    results = [run.results.get(c.id) for c in run.plan]
    passed = sum(1 for r in results if r and r.outcome == PASSED)
    failed = sum(1 for r in results if r and r.failed)
    other = len(run.plan) - passed - failed

    noun = "case" if len(run.plan) == 1 else "cases"
    tally = (f'<span class="pill"><b>{len(run.plan)}</b> {noun}</span>'
             f'<span class="pill ok"><b>{passed}</b> passed</span>')
    if failed:
        tally += f'<span class="pill bad"><b>{failed}</b> failed</span>'
    if other:
        tally += f'<span class="pill"><b>{other}</b> not checked</span>'

    cases = "".join(_case_html(r, shots_dir) for r in results if r)
    title = html.escape(folder or str(out.parent.name) or "assay")

    out.write_text(
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>assay: {title}</title><style>{_CSS}</style></head><body><main>"
        f"<h1>{title}</h1>"
        f'<p class="sub">assay found every control this page renders, used '
        f"each one, and recorded what happened. It didn't need any tests "
        f"written for the page.</p>"
        f'<div class="tally">{tally}</div>'
        f"{cases}"
        f'<section class="surface"><h2>What the page offers</h2>'
        f"<pre>{html.escape(run.surface.render())}</pre></section>"
        f'<footer>Made by <a href="https://github.com/awss1i/assay">assay'
        f'</a>. '
        f"Each screenshot shows the page as the browser rendered it."
        f"</footer></main></body></html>",
        encoding="utf-8")
    return out
