<h1 align="center">Harness</h1>

<p align="center"><a href="../../README.md">assay</a> › <a href="../README.md">Benchmarks</a> › Harness</p>

<p align="center">The scripts that rerun both benchmarks, and the hand-written answer keys they score against.</p>

---

## Contents

- [Before you start](#before-you-start)
- [Running a set](#running-a-set)
- [What a run writes](#what-a-run-writes)
- [The answer keys](#the-answer-keys)
- [When a run writes nothing](#when-a-run-writes-nothing)
- [Adding a program](#adding-a-program)
- [Building another planted set](#building-another-planted-set)

---

## Before you start

The scorers run assay from this checkout, so install it from the repository's
root and download Chromium.

```bash
pip install -e .
python -m playwright install chromium
```

Neither scorer needs an API key or network. The pages are in the repository
and assay runs them in a local browser.

---

## Running a set

```bash
python benchmarks/harness/generated.py    # the generated set
python benchmarks/harness/planted.py      # the planted set
```

Each scorer prints one line per program as it goes, then a summary line with
the bugs found and the working programs flagged, then a line about the links
assay drew between findings. A full run of the generated set takes over an hour,
because it opens every program in a browser.

These runs are shorter, and they write nothing.

```bash
python benchmarks/harness/generated.py --limit 3                  # the first 3 programs of each cell
python benchmarks/harness/generated.py --cell dsh/gpt-oss-120b    # one cell
python benchmarks/harness/planted.py --limit 2                    # the first 2 broken and the first 2 clean
```

A cell is one coding harness and model, and it lives in
`generated/programs/<harness>/<model>/`. CI runs the two `--limit` commands on
every pull request, to check that the scorers still work against the current
assay.

Each scorer exits with 0 when it flagged no working program, and with 1 when
it flagged one or when it wrote nothing because an answer key was incomplete.

---

## What a run writes

Only a complete run writes anything.

| File | Written by | What it holds |
|---|---|---|
| `benchmarks/generated.md` | `generated.py` | The generated set's page |
| `benchmarks/generated/programs/<harness>/<model>/results.md` | `generated.py` | Every program in one cell, with what a person found and what assay reported |
| `benchmarks/planted.md` | `planted.py` | The planted set's page |
| `benchmarks/harness/results.json` | Both | Each set's headline counts from its last complete run |
| The results table in `README.md` and `benchmarks/README.md` | Both | Every set's counts, read from `results.json` |

Each set's page names the machine it ran on and how long the programs took.

---

## The answer keys

A person writes every judgement. A failure is named by its key,
`rule@what the check did`, as `assay --json` prints it. The keys are used
instead of case ids because adding one check renumbers every check after it.

| File | What it says |
|---|---|
| `generated/programs/<harness>/<model>/truth.txt` | Whether each program works, from a person opening and using it, and what is wrong when it doesn't |
| `generated/programs/<harness>/<model>/verdicts.txt` | Which flag is each broken program's actual bug, and what every other flag on it is |
| `generated/checks/` | Scripts that settled a `truth.txt` line by driving the page |
| `planted/broken/<program>/bugs.md` | The bugs the injector says it planted, in its own words |
| `planted/broken/<program>/verdict.txt` | Which planted bug each flag shows |
| `harness/links.txt` | Which findings assay should group on each program |

A line of `truth.txt` names a program, says `works` or `broken`, and gives
the reason.

```
37_draw2  broken  Undo is one press behind
```

A line of `verdicts.txt` takes one of three forms.

```
<program> found <key> | <note>    this flag is the bug
<program> missed <note>           the bug was not flagged
<program> other <key> | <note>    this flag is something else
```

A line of a planted program's `verdict.txt` takes one of three forms, where
`<n>` is the bug's number in `bugs.md`. `planted/verdict-template.txt` is a
blank one to start from.

```
<n> found <key> | <note>     this flag is planted bug n
<n> missed <note>            planted bug n was not flagged
other <key> | <note>         this flag is something else
```

A line of `links.txt` takes one of three forms. `none` marks a program with
several flags that a person judged should have no links between them.

```
<program> same <finding key> -> <key of the first finding in its group>
<program> load <finding key> -> <key of the case that threw on load>
<program> none
```

---

## When a run writes nothing

A scorer prints its summary and then refuses to write while any of these is
true:

- a program couldn't be checked,
- a verdict names a finding that didn't fail in this run,
- a flag on a broken program has no verdict line,
- a program's links differ from `links.txt`,
- a program drew links that `links.txt` doesn't judge.

It prints how many of each it found. So when a change to assay makes it
report something new on a benchmark program, record by hand what the new
finding is, then run the scorer again.

---

## Adding a program

Adding a program changes the headline numbers, so its answer key is written
by hand like the existing ones.

- **To the generated set.** Put the program in a cell as
  `<number>_<name>/index.html`, open it and use it, and add its line to the
  cell's `truth.txt`. If it's broken, run the scorer, then add a line to
  `verdicts.txt` for every flag assay raised on it.
- **A new harness or model.** Add a folder
  `generated/programs/<harness>/<model>/` with its programs, a `truth.txt`
  and a `verdicts.txt`. The scorer finds cells by walking the tree.
- **To the planted set.** Add the working program under `planted/clean/` and
  the copy with bugs under `planted/broken/`, with the injector's `bugs.md`
  and a `verdict.txt` that covers every bug in it.

---

## Building another planted set

Two scripts in `planted/` built the planted set, and they build another set
the same way. Both call a model, so they need `CEREBRAS_API_KEY` set.

```bash
benchmarks/planted/generate.sh path/to/set/clean
benchmarks/planted/inject.sh path/to/set/clean path/to/set/broken
python benchmarks/harness/planted.py path/to/set --marker name
```

`generate.sh` has one harness and model write a working program for each line
of `planted/objectives.txt`. `inject.sh` has a different harness and model
plant bugs in a copy of each program, following `planted/inject-prompt.txt`,
which names no checker, rule or tool. The scorer writes the new set's page
beside its folder, as `path/to/set.md`.

A clean program found broken before the set was first scored can be left out
by naming it in an `EXCLUDED` file in the set's folder, one
`<kind>/<name> <reason>` per line. The set's page publishes each reason.
