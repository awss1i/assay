# Contributing

Bugs and false alarms go in issues. Changes come as pull requests. Questions
go in [Discussions](https://github.com/awss1i/assay/discussions).

## Contents

- [Issues and Pull Requests](#issues-and-pull-requests)
- [Opening an Issue](#opening-an-issue)
- [Opening a Pull Request](#opening-a-pull-request)
- [Setup](#setup)
- [How the Code Is Laid Out](#how-the-code-is-laid-out)
- [Changing a Rule](#changing-a-rule)
- [Tests](#tests)
- [Benchmarks](#benchmarks)
- [Adding a Harness](#adding-a-harness)
- [Before You Open It](#before-you-open-it)
- [Licence](#licence)

## Issues and Pull Requests

**An issue says something is wrong. A pull request changes something.** That
split decides where everything goes.

- **A bug** is an issue: a crash, a hang, a wrong count, a control assay
  should have driven and did not.
- **A false alarm** is an issue: a page that works, flagged as broken.
- **Everything else is a pull request**: a fix, a new rule, a better
  benchmark number, a feature, support for another harness, a clearer
  sentence in the docs.

**Feature requests are not taken, as issues or in Discussions.** If you want
assay to do something, build it and open a pull request. For anything large,
open a draft pull request early, with the idea and a first commit, so a week
of work does not go into something that will not fit.

## Opening an Issue

Use the form. Blank issues are switched off.

**A bug.** Say what you ran, what assay printed, and what went wrong. The form
asks for `assay --version` and your OS. If the bug depends on the page, attach
the page.

**A false alarm.** **Attach the page**: the HTML, a zip of the folder, or a
link to a repository. Without it a false alarm cannot be reproduced, so it
cannot be fixed. Then the command, what assay printed, and why the page is
right.

A false alarm has never happened on the benchmarks, and it costs more than
anything else assay can do, because it sends someone off to fix code that was
right. It is the most useful issue there is.

**What is not an issue:**

- **A miss.** assay finds a fraction of what is broken, by design. It is a
  quick, cheap, mechanical check, and a page it called clean that turned out
  to be broken is the expected case, not a bug. Catching it is a pull request,
  and a welcome one.
- **A feature request.** See above.
- **A question.** Ask it in
  [Discussions](https://github.com/awss1i/assay/discussions/categories/q-a).
- **A security problem.** Report it privately, as [SECURITY.md](SECURITY.md)
  says.

## Opening a Pull Request

Fork, branch, open a pull request. The template asks what kind it is, and each
kind needs something different:

| Kind | What it needs |
|---|---|
| Bug fix | A test that fails before the fix and passes after. Link the issue if there is one. |
| False-alarm fix | The page from the issue, as a test that must stay clean. Both benchmarks, before and after. |
| Benchmark improvement | Both benchmarks, before and after. It has to catch more without flagging anything that works. |
| Feature | Tests for it. If it changes what counts as a failure, it is a rule: see [Changing a Rule](#changing-a-rule). |
| Plugin or harness support | See [Adding a Harness](#adding-a-harness). |
| Docs | Nothing extra. |

**One change per pull request.** A fix and a refactor in the same diff is two
reviews pretending to be one.

## Setup

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
python -m playwright install chromium
```

The editable install matters. An `assay-ui` installed from PyPI into the same
Python is imported ahead of a plain clone, and every test then runs against
that release instead of your change. Check with
`python -c "import assay; print(assay.__file__)"`: it should point into this
folder.

## How the Code Is Laid Out

**`src/assay/`**, the tool:

- `browser.py` opens a page, measures it, and does things to it. It serves the
  folder over loopback, waits for the page to stop arriving, and reads pixels,
  text, fields and styles. **Everything in it is a measurement.** Nothing in
  it decides whether a program is good.
- `surface.py` turns what the page renders into the controls it offers, and
  derives the plan: the cases that exercise all of them.
- `run.py` is `check()`, the whole run from the outside, and `judge()`, which
  compares the measurements before and after each case and decides whether it
  passed. Most rules live here.
- `qa.py` carries the plan out and keeps the results. It also holds a repair
  loop the command line never uses: without `ask` and `apply` it measures and
  reports and never edits anything.
- `report.py` is the `--report` page.
- `tint.py` is terminal colour, and when not to use it.
- `cli.py` is the `assay` command.

**`plugins/assay/`**, the skill and the plugin:

- `skills/checking-a-page/` is the skill, one markdown file.
- `hooks/pages.py` finds the pages a turn changed by looking at the disk.
- `hooks/check_pages.py` checks them and always says what happened.

**`bench/`** holds the 225 generated programs and their scorer.
**`bench/planted/`** holds the planted-bug set and its own. **`tests/`** is the
suite. **`docs/`** holds the longer pages and the scripts that draw the
README's pictures from real runs.

## Changing a Rule

A rule is anything that decides whether a case failed. Most live in `judge`
in `run.py`, and the plan that exercises them in `surface.py`.

1. **Two tests: a page it should flag and a page it must not.** A pure
   comparison of two measurements belongs in `tests/test_judge.py`, which
   needs no browser. Anything that needs a real page goes in
   `tests/test_end_to_end.py`.
2. **Run both benchmarks** and put the numbers, before and after, in the pull
   request. The suite cannot see a false alarm on a working program. The
   benchmarks can.
3. **A false alarm costs more than a miss.** A rule that catches three more
   bugs and flags one working page is not an improvement.
4. **Say what happened, never a verdict.** The output names what was pressed
   and what followed, *the first press did nothing and the second did
   something, from the same state*, and never *this page is broken*.

## Tests

```bash
pytest -q
```

About twenty minutes, because most of it drives a real browser.
`tests/test_judge.py`, `tests/test_plan.py` and `tests/test_perform.py` need
no browser and run in seconds, which makes them the ones to run while you
work. `tests/test_end_to_end.py` is most of the twenty minutes, and skips
rather than fails where there is no browser.

CI runs the whole suite on Python 3.10, 3.12, 3.13 and 3.14 for every pull
request, plus a three-program run of the benchmark scorer. All of it has to
pass before anything merges.

## Benchmarks

```bash
python bench/score.py            # 225 generated programs, about 75 minutes
python bench/planted/score.py    # 50 planted bugs, about eight minutes
```

Neither needs a key or a network. Paste the summary line each one prints into
the pull request, before and after your change.

Adding a program changes the headline numbers, so its answer key is written
by hand, the way every existing one was. [bench/README.md](bench/README.md)
and [bench/planted/README.md](bench/planted/README.md) say how each set was
built.

## Adding a Harness

- **If the harness reads skills,** add its install steps to
  [docs/harnesses.md](docs/harnesses.md), pointing at
  `plugins/assay/skills/checking-a-page/`.
- **If it has its own plugin format,** add its marketplace file beside the
  others (`.claude-plugin/`, `.cursor-plugin/`, `.grok-plugin/`,
  `.agents/plugins/`, `.github/plugin/`) and document it in the same place.
- **Try it on the harness itself** and say which version you used.
- **Update the count.** The README and the harness page both say how many
  harnesses there are.
- **It reports and never fixes.** The skill and the plugin hand over what was
  pressed and what happened, and do not edit code on the strength of it. Keep
  it that way.

## Before You Open It

- The tests for what you changed pass, or you changed only docs.
- A change to a rule or to `bench/` has both benchmark numbers, before and
  after.
- One change per pull request.
- Commit messages say where and what, lowercase: `readme: add X badge`,
  `docs: correct the harness count`.

## Licence

assay is MIT licensed, and contributions are accepted under the same licence.
