<h1 align="center">Usage</h1>

<p align="center"><a href="../README.md">assay</a> › Usage</p>

<p align="center"><b>English</b> · <a href="usage.zh-CN.md">简体中文</a> · <a href="usage.ja.md">日本語</a> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>

<p align="center">Every option of the assay command, what it prints, its exit codes, the HTML report and the Python API.</p>

---

## Contents

- [The command](#the-command)
- [Options](#options)
- [What assay prints](#what-assay-prints)
  - [The default output](#the-default-output)
  - [The short summary](#the-short-summary)
  - [JSON](#json)
  - [The controls](#the-controls)
- [Exit codes](#exit-codes)
- [The HTML report](#the-html-report)
- [Colour](#colour)
- [Errors](#errors)
- [From Python](#from-python)
  - [Checking a page](#checking-a-page)
  - [Acceptance criteria](#acceptance-criteria)
  - [Listing the controls](#listing-the-controls)

---

## The command

```console
assay ./my-app                    # check index.html in this folder
assay ./my-app/todo.html          # check a specific page
assay ./my-app -e app.html        # or name the page inside a folder

assay ./my-app --report out.html  # also write an HTML report with screenshots
assay ./my-app --json             # print the full run as JSON
assay ./my-app --one-line         # short summary, for scripts and agents
assay ./my-app --surface          # list the controls it found, then stop
```

assay takes one path. When the path is a folder, assay serves the folder and
opens `index.html` in it. When the path ends in `.html`, `.htm` or `.xhtml`,
that file is the page, and assay serves the folder it's in, because a page
loads the files beside it.

The exit code is non-zero if anything failed. Apart from the Chromium download on the first run, nothing is written to disk unless you ask.

---

## Options

| Option | What it does |
|---|---|
| `-e ENTRY`, `--entry ENTRY` | Opens `ENTRY` inside the folder instead of `index.html` |
| `--report FILE` | Also writes an HTML report to `FILE`, with screenshots of the page before and after each check |
| `--json` | Prints the whole run as JSON instead of the default output |
| `--one-line` | Prints a short summary of what was checked and what was flagged |
| `--if-page` | Prints nothing and exits with 0 unless the path is a page assay can check |
| `--surface` | Prints the controls the page offers and stops, without running any checks |
| `--version` | Prints the installed version and exits |
| `-h`, `--help` | Prints the options and exits |

`--if-page` is for hooks that run after every edit. Most edits aren't to a
page, and with this option assay stays silent for those instead of printing
an error into the agent's conversation.

When `--json` and `--one-line` are both given, assay prints JSON.

---

## What assay prints

### The default output

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

The first line counts the checks planned, carried out, passed and failed.
Every check follows in the order it ran, as its number, its outcome and what
it did.

| Outcome | What it means |
|---|---|
| `[ok]` | The check ran and nothing was wrong |
| `[FAILED]` | A rule was broken, and the line starting with `→` says what happened |
| `[not checked]` | The check couldn't be carried out, which never counts as a failure |

A failure that repeats an earlier finding shows `↳ same finding as C003`
instead of the message, and the first line says how many failures are
repeats.

Checks are numbered `C001`, `C002` and so on. Findings about the whole run,
which no single check could show, are numbered `F001`, `F002`, and the two
findings about the whole page are `C000`.

---

### The short summary

`--one-line` prints one sentence when nothing is flagged.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

When something is flagged, it prints one line per finding, and a repeat
names the first finding instead of repeating its message.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

When some checks couldn't be carried out, the first line says how many, so a
page isn't reported clean because of checks that never ran. Text that comes
from the page is flattened to one line of printable characters, so a page
can't add a line of its own to the summary.

---

### JSON

`--json` prints one object with these fields.

| Field | What it holds |
|---|---|
| `version` | The assay version |
| `entry` | The page that was opened |
| `planned`, `passed`, `failed` | How many checks were planned, passed and failed |
| `works` | `true` when no check failed |
| `sandboxed` | `true` when the page ran inside Chromium's sandbox |
| `surface` | Every control found, with its `kind`, `selector`, `label` and whether it's `enabled` |
| `cases` | Every check, described below |
| `links` | Every link between findings, as `from`, `kind`, `to` and `why` |
| `console_errors` | Errors the page logged to the console |
| `failed_requests` | Requests the page made that failed |

Each entry in `cases` has these fields.

| Field | What it holds |
|---|---|
| `id` | The check's number, such as `C003` |
| `what` | What the check did, in words |
| `outcome` | `passed`, `failed` or `unknown`, where `unknown` means not checked |
| `detail` | What went wrong, for a failed check |
| `measured` | What assay measured, whether the check passed or failed |
| `acts` | The actions the check carried out, in order |
| `rules` | The names of the rules the check broke |
| `key` | A name for the finding that stays the same when checks are added, as `rule@what the check did` |
| `links` | The links from this finding to another, as `kind`, `to` and `why` |

Console errors and failed requests never fail a check, because a page can log
an error or miss an icon and still work. They're often the first thing worth
reading when a check did fail.

---

### The controls

`--surface` lists what assay found on the page, one control per line, with
its kind, its selector, its label and its size in pixels.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter --surface
kind: page
- button `#inc` 'Increment' 151x52
- button `#reset` 'Reset' 107x52
```

---

## Exit codes

| Code | When |
|---|---|
| 0 | No check failed |
| 1 | At least one check failed |
| 2 | The page couldn't be checked, because it doesn't exist, needs a build, or Chromium couldn't be installed |

With `--if-page`, assay exits with 0 instead of 2. `--surface` exits with 0
once it has listed the controls.

---

## The HTML report

`--report` writes a page you can open, showing the page before and after every check.

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="One check from an assay report on a
tag filter, where the tag was clicked twice, it went back to how it looked,
and the list stayed filtered. The check is shown with its actions, its reason,
and screenshots of the page before and after, twelve items and then one.">

For each check, the report shows its actions, its outcome and reason, and
what assay measured. It's one HTML file, with the screenshots in a folder
beside it named after the report, so `--report out.html` also writes
`out-shots/`. The report loads nothing from the internet, so it opens
straight from disk or from a CI artifact, and it follows your light or dark
theme.

---

## Colour

In a terminal, assay colours the outcomes so failures stand out. Output sent
to a pipe or a file has no colour. Setting the `NO_COLOR` environment
variable turns colour off, and setting `FORCE_COLOR` turns it on anywhere.

---

## Errors

assay prints these on the error stream.

| Message | What it means |
|---|---|
| `assay: my-app/index.html doesn't exist` | The path has no page to open |
| `assay: index.html loads /src/main.jsx, which a browser can't run without a build step.` | The folder is a source tree. assay prints the build command to run yourself, and never runs it |
| `assay: index.html loads /src/main.jsx, which a browser can't run, but dist/index.html is built.` | The folder has a built copy, and assay prints the path to check instead |
| `assay: there's no index.html here, but there's a package.json, so the page probably comes from a build step.` | The folder is a project that hasn't been built |
| `assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.` | The first run is downloading Chromium |
| `assay: playwright isn't installed. Run pip install assay-ui to install it.` | assay's own dependency is missing from this Python |
| `assay: Chromium's sandbox couldn't start on this system, so the page ran without it.` | The page was still checked. The sandbox can't start when running as root or in some containers |

When a single check can't be carried out, the run goes on, and that check is
reported as not checked with the reason, such as a page that replaces a
built-in function assay relies on.

---

## From Python

### Checking a page

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

`check` takes these arguments.

| Argument | What it does |
|---|---|
| `folder` | The folder holding the page, or the page itself, read the way the command reads its path |
| `entry` | The page to open inside the folder. The default is `index.html` |
| `criteria` | Checks of your own to run before assay's, described below |
| `shots` | A folder for a screenshot before and after each check. Without it, nothing is written to disk |

It returns a report with these attributes.

| Attribute | What it holds |
|---|---|
| `works` | `True` when no check failed |
| `plan` | Every check, in the order it ran |
| `results` | Each check's result, by the check's number |
| `failing` | The failed results, with your own criteria first |
| `unchecked` | The results for checks that couldn't be carried out |
| `surface` | The controls assay found |
| `console_errors`, `failed_requests` | What the page logged and the requests that failed |
| `summary()`, `render()` | The first line of the output, and the whole output, as text |

Each result has the `case` it ran, an `outcome` of `"passed"`, `"failed"` or
`"unknown"`, the `detail` of what went wrong, the `evidence` assay measured,
the `rules` it broke and its `key`.

---

### Acceptance criteria

assay doesn't know what a control is meant to do, so a page that runs but
does the wrong thing usually passes. To check what the page should do, write
a check of your own and pass it as a criterion.

```python
from assay import Case, check

total = Case(
    id="A001",
    what="adding 10 and 20 shows a total of 30",
    acts=[{"fill": "#price=10"}, {"click": "#add"},
          {"fill": "#price=20"}, {"click": "#add"}],
    expect={"want": "Total: 30"},
    origin="criterion",
)

report = check("./my-app", criteria=[total])
```

On a page that adds wrongly, the criterion fails with this detail.

```
the page doesn't contain 'Total: 30'
```

`acts` are the actions to carry out, in order. Each one is a verb and its
target.

| Action | What it does |
|---|---|
| `{"click": "#add"}` | Clicks the element the selector matches. The words on a control work too, as in `{"click": "Add"}` |
| `{"fill": "#price=10"}` | Types the value after `=` into the field the selector matches |
| `{"press": "Enter"}` | Presses a key |
| `{"reload": "page"}` | Reloads the page |
| `{"wait": "2"}` | Waits that many seconds, up to 10 |

`expect` says what has to be true afterwards.

| Expectation | What has to be true |
|---|---|
| `{"want": "Total: 30"}` | The text appears on the page |
| `{"unchanged": True}` | The page stays as it was |
| `{"quiet": True}` | Nothing in particular, so the check only fails if the page throws an error |
| `{}` | Something on the page changes |

assay numbers every check itself, so a criterion's `id` is replaced in the
results. `--json` prints the `acts` of every check assay plans, which shows
how assay writes each kind of action.

---

### Listing the controls

`look` opens the page and lists its controls without running any checks, the
way `--surface` does.

```python
from assay import look

opened = look("./my-app")
print(opened.surface.render())
```
