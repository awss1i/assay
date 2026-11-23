<h1 align="center">Getting started</h1>

<p align="center"><a href="../README.md">assay</a> › Getting started</p>

<p align="center"><b>English</b> · <a href="getting-started.zh-CN.md">简体中文</a> · <a href="getting-started.ja.md">日本語</a> · <a href="getting-started.ko.md">한국어</a> · <a href="getting-started.ru.md">Русский</a></p>

<p align="center">From installing assay to using it every day.</p>

---

## Contents

- [Before you start](#before-you-start)
- [Checking a page](#checking-a-page)
- [Reading the result](#reading-the-result)
- [A page with a bug](#a-page-with-a-bug)
- [Choosing the page](#choosing-the-page)
- [The HTML report](#the-html-report)
- [A short summary](#a-short-summary)
- [With a coding agent](#with-a-coding-agent)
- [Where to go next](#where-to-go-next)

---

## Before you start

You need Python 3.10 or newer, and a page a browser can open, which means a
folder with an `.html` file in it.

```bash
pip install assay-ui
```

If your project has a build step, build it first and check the output folder.
assay never runs a build itself.

[All install options](install.md)

---

## Checking a page

Point assay at the folder that holds your page.

```console
assay ./my-app
```

The first run downloads Chromium, which happens once. Then assay serves the
folder on localhost, opens `index.html` in Chromium, lists every control the
page renders, plans its checks from those controls, and runs each check in a
fresh tab. Most pages take a few seconds to a minute.

The repository holds the pages assay is scored on, so in a clone of it you
can run the examples on this page as they are. This one is a click counter
that works.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter
7 cases planned, 7 carried out, 7 passed, 0 failed

C001 [ok] open the page and let it settle
C002 [ok] press Increment
C003 [ok] press Increment twice
C004 [ok] press Reset
C005 [ok] press Reset twice
C006 [ok] press Increment, then Reset
C007 [ok] press Reset, then Increment
```

---

## Reading the result

The first line counts the checks assay planned, how many it could carry out,
and how many passed and failed. Each line after it is one check, with its
number, its outcome and what the check did.

| Outcome | What it means |
|---|---|
| `[ok]` | The check ran and nothing was wrong |
| `[FAILED]` | The page contradicted itself, and the line under the check says how |
| `[not checked]` | assay couldn't carry the check out, which never counts as a failure |

The exit code is 0 when nothing failed, 1 when a check failed, and 2 when the
page couldn't be checked at all, so a script can act on it.

Apart from the Chromium download on the first run, assay writes nothing to
disk unless you ask.

---

## A page with a bug

This one is a small drawing program whose Undo reacts a press late.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

C016 is the failure. The first Undo did nothing and the second did the work,
so Undo is one press behind.

When one bug fails several checks, the first failure shows the message and
the rest point back to it, so you read the message once.

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

assay doesn't know what your page is for, so a finding is a place to look,
not a confirmed bug. A control can correctly do nothing in the state it was
pressed in.

---

## Choosing the page

```console
assay ./my-app                    # check index.html in this folder
assay ./my-app/todo.html          # check a specific page
assay ./my-app -e app.html        # or name the page inside a folder
```

assay checks one page at a time, served from a local folder. If you point it
at a source tree that needs a build, it tells you what to run.

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

## The HTML report

`--report` writes a page you can open, showing the page before and after every check.

```console
assay ./my-app --report out.html
```

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="One check from an assay report on a
tag filter, where the tag was clicked twice, it went back to how it looked,
and the list stayed filtered. The check is shown with its actions, its reason,
and screenshots of the page before and after, twelve items and then one.">

The report is one HTML file, with its screenshots in a folder beside it
named after the report, here `out-shots`.

---

## A short summary

`--one-line` prints a short summary, for scripts and agents.

```console
$ assay ./todo --one-line
assay: checked todo/index.html, 8 checks, nothing flagged.
```

When something is wrong, the summary lists each finding, and a repeat names
the first finding instead of repeating its message.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

---

## With a coding agent

assay comes with two things for coding agents.

The **skill** tells your agent to run assay after it finishes a page, and to
end its reply with the result.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

The **plugin** adds a hook that runs the check automatically at the end of
each turn that changed a page. In Claude Code, these two commands install the
skill and the hook together.

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

Either way, the agent reports what assay found and doesn't change code
because of it unless you ask.

[Harnesses](harnesses.md) · [The Skill & Plugin](../plugins/assay/README.md)

---

## Where to go next

The docs cover every option and the Python API, every check assay makes and
the message it prints, and the setup for each coding agent harness.

[Docs](../README.md#docs)
