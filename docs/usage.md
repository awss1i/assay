<h1 align="center">Using assay</h1>

---

<p align="center">Everything assay does from the command line and from Python.</p>

---

## Contents

- [The command](#the-command)
- [An example](#an-example)
- [The HTML report](#the-html-report)
- [From Python](#from-python)

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

Nothing is written to disk unless you ask, and the exit code is non-zero if anything failed.

---

## An example

assay ships with the benchmark pages it is scored on, so you can run it on one
right now. This one is a small drawing program whose Undo reacts a press late:

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 case(s) planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → pressing this twice from the same starting point, the first press changed nothing and the second did, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

C016 is the failure. The first Undo did nothing and the second did the work, so
Undo is one press behind.

---

## The HTML report

`--report` writes a page you can open, showing the page before and after every check:

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="One check from an assay report on a
tag filter, where the tag was clicked twice, it went back to how it looked,
and the list stayed filtered. Shown with the actions, the reason, and
screenshots of the page before and after, twelve items and then one.">

---

## From Python

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```
