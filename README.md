# assay

[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://github.com/awss1i/assay/blob/main/pyproject.toml)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/awss1i/assay/blob/main/LICENSE)
[![X](https://img.shields.io/badge/follow-@awss1i-blue?logo=x)](https://x.com/awss1i)

**Drives your web page in a real browser and tells you what broke. No tests to write, no LLM.**

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/run.svg" alt="A terminal running assay on a list
you reorder by dragging. 7 checks planned from the page, 1 passed and 6
failed. The first failure says nothing on the page changed at all, and the
other five say they are the same finding.">

<p align="center"><i>Checking a drag-to-reorder list with a bug in it.</i> <code>pip install assay-ui</code></p>

assay opens your page in Chromium, finds every control on it, uses all of
them, and reports what went wrong.

- **No tests to write.** assay builds its checks from the controls it finds
  on the page.
- **No LLM.** There's no API key and no cost, and every run gives the same
  result.
- **Works with coding agents.** A skill tells the agent in fifteen harnesses
  to check each page it writes, and a plugin for Claude Code and the DeepSeek
  Harness does it automatically after every turn.
- **Groups repeats.** When one bug fails several checks, the later ones say
  *same finding as C003* instead of repeating the message.

## Contents

- [Install](#install)
  - [For coding agents](#for-coding-agents)
- [Use](#use)
  - [With coding agents](#with-coding-agents)
- [Benchmarks](#benchmarks)
  - [Pages written by AI](#pages-written-by-ai)
  - [Pages with bugs added on purpose](#pages-with-bugs-added-on-purpose)
  - [How grouping is checked](#how-grouping-is-checked)
- [How It Works](#how-it-works)
- [Why](#why)
- [Limits](#limits)
- [Contributing](#contributing)
- [Licence](#licence)

## Install

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # no Python 3.10+? uv downloads one
```

```bash
pipx install assay-ui          # its own environment, for when pip says "externally managed"
```

If `pip` isn't found, use `python3 -m pip install assay-ui`. The first run
downloads Chromium if needed.

To work on assay itself:

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
```

### For coding agents

Install the CLI above first, then follow the
**[harness setup →](https://github.com/awss1i/assay/blob/main/docs/harnesses.md)**
to add the skill or plugin in any of the fifteen supported harnesses.

## Use

```console
assay ./my-app                    # check index.html in this folder
assay ./my-app/todo.html          # check a specific page
assay ./my-app -e app.html        # or name the page inside a folder

assay ./my-app --report out.html  # also write an HTML report with screenshots
assay ./my-app --json             # print the full run as JSON
assay ./my-app --one-line         # short summary, for scripts and agents
assay ./my-app --surface          # list the controls it found, then stop
```

This repository includes a drawing program whose Undo is broken:

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 case(s) planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → pressing this twice from the same starting point, the first press changed nothing and the second did, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

Nothing is written to disk unless you ask. The exit code is non-zero if
anything failed. `--report` shows the page before and after every check:

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="One check from an assay report on a
tag filter, where the tag was clicked twice, it went back to how it looked,
and the list stayed filtered. Shown with the actions, the reason, and
screenshots of the page before and after, twelve items and then one.">

From Python:

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

### With coding agents

The **skill** works in all fifteen supported harnesses: Claude Code, DeepSeek
Harness, opencode, Antigravity, Codex App, Codex CLI, Cursor, Devin CLI,
Factory Droid, Gemini CLI, GitHub Copilot CLI, Grok Build CLI, Kimi Code, Pi
and Hermes Agent. It tells your agent to run assay after finishing a page and
end its reply with the result:

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

The **plugin** (Claude Code and the DeepSeek Harness) adds a hook that runs
the check automatically at the end of each turn that changed a page. Either
way, the agent reports what assay found and doesn't change code because of it
unless you ask.

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

**[How the skill and plugin work →](https://github.com/awss1i/assay/blob/main/plugins/assay/README.md)**

## Benchmarks

assay is scored on two sets of pages. Both are in this repository, every
number below is written by the scoring script rather than typed by hand, and
neither script needs an API key or network.

### Pages written by AI

225 small web apps that an AI model wrote from 75 prompts (a to-do list, a
paint program, a seat map, and so on), three times each: through two coding
tools and on its own. A person opened and tried every one first: 20 are
broken and 205 work.

<!-- generated -->

- **Found:** the actual bug on 15 of the 20 broken pages. A flag only counts if it's that page's bug.
- **False alarms:** 0 of the 205 working pages flagged.
- **Grouping:** 51 of the 51 links assay drew between findings match the hand-written answer key, and 0 that the key expects are missing.
- **Speed:** a median of 14 seconds a page, and 221 of the 225 finish inside a minute.

<!-- /generated -->

Run it: `python bench/score.py` (about 75 minutes).
**[Every page and result →](https://github.com/awss1i/assay/blob/main/bench/README.md)**

### Pages with bugs added on purpose

10 working apps, plus a copy of each where a different AI model added 5 bugs
and wrote down what they were.

<!-- planted -->

- **Found:** 12 of the 50 added bugs.
- **False alarms:** 0 of the 10 original pages flagged.
- **Grouping:** 10 of the 10 links assay drew between findings match the hand-written answer key, and 0 that the key expects are missing.

<!-- /planted -->

About half the bugs it misses make a page show a wrong value, like a total
that's off by one or a swatch that doesn't match its sliders. assay can't
judge a value without knowing what the page is for, which is what acceptance
criteria are for. Most of the rest only show up with an input or a step it
didn't try.

Run it: `python bench/planted/score.py` (about 8 minutes).
**[Every bug and result →](https://github.com/awss1i/assay/blob/main/bench/planted/README.md)**

### How grouping is checked

A link is a *same finding as C003* line, or a note that the page crashed
while loading. The answer key,
[`bench/links.txt`](https://github.com/awss1i/assay/blob/main/bench/links.txt),
was written by hand from what each failure actually is: which failures on a
page are the same bug, and which pages have unrelated failures that must not
be grouped. Both scripts check every link assay draws against it, and refuse
to write their results if one is wrong.

## How It Works

1. Serves the folder on localhost and opens the page in Chromium.
2. Waits until the page's controls stop changing.
3. Lists every control the browser renders, including clickable divs, drag
   handles and editable regions.
4. Plans checks from those controls: press every button once and twice,
   type empty, ordinary, very long and HTML-laden text into fields, change
   every dropdown, draw on canvases, fill in and submit forms, and more.
5. Runs each check in a fresh tab and compares the page before and after.

assay doesn't know what your page is for, so a button that changes nothing
isn't a failure by itself. Instead it reports places where the page
contradicts itself. For example:

- the page throws an error,
- Undo does nothing on the first press and works on the second,
- a count of items shows 1 when the list is empty,
- a total goes up when an item is added but not down when one is removed,
- `NaN` appears where a number should be,
- nothing on the page responds to any control.

**[Every rule →](https://github.com/awss1i/assay/blob/main/docs/how-it-works.md)**

## Why

Playwright and Cypress need tests someone wrote. Visual regression needs a
reference screenshot. Asking a model to review the code means reading it, not
running it. assay runs it, with nothing prepared in advance.

|  | needs tests written | needs a baseline | runs the program |
|---|---|---|---|
| Playwright / Cypress | yes | no | yes, the parts you wrote |
| Percy / Chromatic | no | **yes** | it screenshots it |
| ask a model to review it | no | no | **no, it reads the source** |
| **assay** | **no** | **no** | **yes, all of it** |

## Limits

- **It can't check intent.** A page that runs but does the wrong thing, like
  a total that adds wrongly, usually passes. To check that, pass acceptance
  criteria from Python.
- **Web pages only.** It checks one page at a time, served from a local
  folder. It doesn't crawl, log in or use live network calls.
- **Built output only.** It won't run `npm install` or your build. Point it
  at a source tree and it tells you what to run first.
- **A finished game can look broken.** A game that has ended with no way to
  restart stops responding, and that can be reported as nothing responding.
- **Speed.** Most pages take a few seconds to a minute. The benchmark page
  has every page's time and the machine they were measured on.

## Contributing

Report bugs and false alarms as issues, send changes as pull requests, and ask
questions in [Discussions](https://github.com/awss1i/assay/discussions). See
**[CONTRIBUTING.md](https://github.com/awss1i/assay/blob/main/CONTRIBUTING.md)**.

## Licence

MIT.
