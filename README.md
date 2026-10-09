<h1 align="center">assay</h1>

<p align="center">
  <a href="https://github.com/awss1i/assay/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="python"></a>
  <a href="https://github.com/awss1i/assay/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-MIT-blue" alt="licence"></a>
  <a href="https://github.com/sickn33/agentic-awesome-skills"><img src="https://img.shields.io/badge/listed%20in-agentic--awesome--skills-blue" alt="listed in agentic-awesome-skills"></a>
</p>

<p align="center">
  <a href="#install">Install</a> · <a href="#use">Use</a> · <a href="#benchmarks">Benchmarks</a> · <a href="#how-it-works">How it works</a> · <a href="#why">Why</a> · <a href="#limits">Limits</a> · <a href="#contributing">Contributing</a> · <a href="#licence">Licence</a>
</p>

<p align="center"><strong>Drives your web page in a real browser and tells you what broke. No tests to write, no LLM.</strong></p>

<p align="center"><code>pip install assay-ui</code></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/run.svg" alt="A terminal running assay on a list
you reorder by dragging. 7 checks planned from the page, 1 passed and 6
failed. The first failure says nothing on the page changed at all, and the
other five say they are the same finding.">
</p>

<p align="center"><i>Checking a drag-to-reorder list with a bug in it.</i></p>

---

assay opens your page in Chromium, finds every control on it, uses all of
them, and reports what went wrong.

- **No tests to write.** assay builds its checks from the controls it finds
  on the page.
- **No LLM.** There's no API key and no cost, and every run gives the same
  result.
- **Works with coding agents.** A skill, supported across fifteen harnesses,
  has the agent check each page it writes, and a plugin for Claude Code and the
  DeepSeek Harness runs the check automatically after every turn.
- **Groups repeats.** When one bug fails several checks, the later ones say
  *same finding as C003* instead of repeating the message.

---

## Install

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # no Python 3.10+? uv downloads one
```

```bash
pipx install assay-ui          # installs assay in its own isolated environment
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

---

## Use

```console
assay ./my-app                    # check index.html in this folder
assay ./my-app --report out.html  # also write an HTML report with screenshots
assay ./my-app --one-line         # short summary, for scripts and agents
```

The exit code is non-zero if anything failed, and nothing is written to disk
unless you ask.

**[The full flags, a worked example, the Python API and the HTML report →](https://github.com/awss1i/assay/blob/main/docs/usage.md)**

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

---

## Benchmarks

Scored on two sets of pages in this repository. Every number here is written
by the scoring script, never typed by hand.

**Pages written by AI.** 225 small web apps an AI wrote from 75 prompts, three
times each, which a person then opened and tried.

<!-- generated -->

Found the real bug on 15 of the 20 broken pages, with 0 of the 205 working pages flagged. [Every page and result](https://github.com/awss1i/assay/blob/main/bench/README.md).

<!-- /generated -->

**Pages with bugs added on purpose.** 10 working apps, each copied with 5 bugs
added and written down.

<!-- planted -->

Found 12 of the 50 added bugs, with 0 of the 10 original pages flagged. [Every bug and result](https://github.com/awss1i/assay/blob/main/bench/planted/README.md).

<!-- /planted -->

---

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

---

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

---

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

---

## Contributing

Report bugs and false alarms as issues, send changes as pull requests, and ask
questions or share ideas in [Discussions](https://github.com/awss1i/assay/discussions). See
**[CONTRIBUTING.md](https://github.com/awss1i/assay/blob/main/CONTRIBUTING.md)**.

---

## Licence

MIT.
