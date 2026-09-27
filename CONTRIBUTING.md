# Contributing

Report bugs and false alarms as issues, send changes as pull requests, and ask
questions in [Discussions](https://github.com/awss1i/assay/discussions).

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

An issue reports that something is wrong. A pull request changes something.

- **A bug** is an issue: a crash, a hang, a wrong count, or a control assay
  should have used and didn't.
- **A false alarm** is an issue: a working page flagged as broken.
- **Everything else is a pull request**: a fix, a new rule, a better
  benchmark number, a feature, support for another harness, or a docs
  improvement.

Feature requests aren't taken as issues or in Discussions. If you want assay
to do something, build it and open a pull request. For anything large, open a
draft pull request early with the idea and a first commit, so we can agree on
the approach before you spend a lot of time on it.

## Opening an Issue

Use the issue form (blank issues are turned off).

**A bug.** Say what you ran, what assay printed, and what went wrong. The form
asks for `assay --version` and your OS. If the bug depends on the page, attach
the page.

**A false alarm.** Attach the page: the HTML, a zip of the folder, or a link to
a repository. Without it the false alarm can't be reproduced or fixed. Include
the command, what assay printed, and why the page is correct.

A false alarm has never happened on the benchmarks, and it costs more than
anything else assay can do, because it sends someone to change code that was
right. That makes it the most useful issue you can open.

**Not an issue:**

- **A miss.** assay is a quick mechanical check and misses many bugs by
  design. Teaching it to catch one is a welcome pull request.
- **A feature request.** See above.
- **A question.** Ask in
  [Discussions](https://github.com/awss1i/assay/discussions/categories/q-a).
- **A security problem.** Report it privately, as
  [SECURITY.md](SECURITY.md) describes.

## Opening a Pull Request

Fork, branch, and open a pull request. The template asks what kind it is:

| Kind | What it needs |
|---|---|
| Bug fix | A test that fails before the fix and passes after. Link the issue if there is one. |
| False-alarm fix | The page from the issue, as a test that must stay clean. Both benchmarks, before and after. |
| Benchmark improvement | Both benchmarks, before and after. It must catch more without flagging anything that works. |
| Feature | Tests. If it changes what counts as a failure, it's a rule: see [Changing a Rule](#changing-a-rule). |
| Plugin or harness support | See [Adding a Harness](#adding-a-harness). |
| Docs | Nothing extra. |

One change per pull request: send a fix and a refactor separately.

## Setup

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
python -m playwright install chromium
```

Use the editable install. If `assay-ui` from PyPI is installed in the same
Python, it's imported instead of your clone and the tests run against the
release. Check with `python -c "import assay; print(assay.__file__)"`: it
should point into this folder.

## How the Code Is Laid Out

**`src/assay/`**, the tool:

- `browser.py` serves the folder, opens the page, waits for it to load, and
  reads pixels, text, fields and styles. It only measures; it never decides
  whether something failed.
- `surface.py` turns the rendered page into a list of controls and builds the
  plan of checks.
- `run.py` holds `check()`, which runs everything, and `judge()`, which
  compares the page before and after each check and decides whether it
  passed. Most rules live here.
- `qa.py` runs the plan and keeps the results. It has no browser code, so it
  can be tested without one.
- `links.py` groups failures that are the same finding. It reads finished
  results and never changes an outcome.
- `report.py` writes the `--report` page.
- `tint.py` handles terminal colour.
- `cli.py` is the `assay` command.

**`plugins/assay/`**, the skill and the plugin:

- `skills/checking-a-page/` is the skill, one markdown file.
- `hooks/pages.py` finds the pages a turn changed, by file times.
- `hooks/check_pages.py` checks them and always reports the result.

**`bench/`**:

- `programs/` holds the 225 generated programs, scored by `score.py`.
- `planted/` holds the planted-bug set and its own `score.py`.
- `links.txt` is the answer key for grouped findings.
- `checks/` holds scripts that confirmed answer-key entries by driving the
  pages.

**`tests/`** is the test suite. **`docs/`** holds the longer pages and the
scripts that draw the README's pictures from real runs.

## Changing a Rule

A rule is anything that decides whether a check failed. Most live in `judge`
in `run.py`; the checks that exercise them are built in `surface.py`.

1. **Write two tests:** a page it should flag and a page it must not. Pure
   comparisons go in `tests/test_judge.py`, which needs no browser. Anything
   needing a real page goes in `tests/test_end_to_end.py`.
2. **Run both benchmarks** and put the before and after numbers in the pull
   request. The tests can't see a false alarm on a working program; the
   benchmarks can.
3. **A false alarm costs more than a miss.** A rule that catches three more
   bugs but flags one working page is not an improvement.
4. **Say what happened, in plain words.** A message says what assay did and
   what the page did in response, like *pressing this twice from the same
   starting point: the first press changed nothing and the second did, so it
   reacts one press late*. It never gives a bare verdict like *this page is
   broken*, and it should make sense to someone who hasn't read the rule.
5. **Document it.** Add the rule to [docs/how-it-works.md](docs/how-it-works.md)
   under the action that triggers it: what assay does, the message it prints,
   and when it stays quiet and why.

## Tests

```bash
pytest -q
```

The full suite takes about 25 minutes, because most tests drive a real
browser. `tests/test_judge.py`, `tests/test_plan.py`, `tests/test_links.py`
and `tests/test_perform.py` need no browser and run in seconds, so run those
while you work. `tests/test_end_to_end.py` takes most of the time, and skips
rather than fails when there's no browser.

CI runs the whole suite on Python 3.10, 3.12, 3.13 and 3.14 for every pull
request, plus a short run of both benchmark scorers. All of it must pass
before anything is merged.

## Benchmarks

```bash
python bench/score.py            # the 225 generated programs
python bench/planted/score.py    # the planted-bug set
```

Neither needs an API key or network. Each writes a README with its results,
including how long every program took and the machine it ran on. Paste the
summary line each one prints into your pull request, before and after your
change.

**Judgements are written by hand.** Each failure is named by its key,
`rule@what the check did`, as `assay --json` prints it. Keys are used instead
of case ids because adding one check renumbers every check after it.

- `bench/programs/<harness>/<model>/verdicts.txt` says which flag is each
  broken program's actual bug, and what every other flag on it is.
- `bench/planted/broken/*/verdict.txt` says which planted bug each flag shows.
- `bench/links.txt` says which findings should be grouped on each program.

A scorer won't write its results while a verdict names a failure that didn't
happen, a flag on a broken program has no verdict, or a grouping is wrong or
unjudged. So if your change makes assay report something new, you also need
to record by hand what it is.

Adding a program changes the headline numbers, so its answer key has to be
written by hand like the existing ones. [bench/README.md](bench/README.md)
and [bench/planted/README.md](bench/planted/README.md) describe how each set
was built.

## Adding a Harness

- **If the harness reads skills,** add its install steps to
  [docs/harnesses.md](docs/harnesses.md), pointing at
  `plugins/assay/skills/checking-a-page/`.
- **If it has its own plugin format,** add its marketplace file next to the
  others (`.claude-plugin/`, `.cursor-plugin/`, `.grok-plugin/`,
  `.agents/plugins/`, `.github/plugin/`) and document it in the same place.
- **Test it in the harness** and say which version you used.
- **Update the count.** The README and the harness page both say how many
  harnesses are supported.
- **It reports and never fixes.** The skill and plugin pass on what was
  pressed and what happened, and don't edit code because of it. Keep it that
  way.

## Before You Open It

- The tests for what you changed pass, or you only changed docs.
- A change to a rule or to `bench/` includes both benchmark numbers, before
  and after.
- One change per pull request.
- Commit messages say where and what, in lowercase: `readme: add X badge`,
  `docs: correct the harness count`.

## Licence

assay is MIT licensed, and contributions are accepted under the same licence.
