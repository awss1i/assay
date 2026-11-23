<h1 align="center">Development</h1>

<p align="center"><a href="../README.md">assay</a> › Development</p>

<p align="center"><b>English</b> · <a href="development.zh-CN.md">简体中文</a> · <a href="development.ja.md">日本語</a> · <a href="development.ko.md">한국어</a> · <a href="development.ru.md">Русский</a></p>

<p align="center">How assay's code is laid out, and what each kind of change to it needs.</p>

---

## Contents

- [How the code is laid out](#how-the-code-is-laid-out)
- [Changing a rule](#changing-a-rule)
- [Tests](#tests)
- [Benchmarks](#benchmarks)
- [Adding a harness](#adding-a-harness)
- [Changing the docs](#changing-the-docs)
- [Docs](#docs)

---

## How the code is laid out

**`src/assay/`**, the tool:

- `browser.py` serves the folder, opens the page, waits for it to load, and
  reads pixels, text, fields and styles. It only measures, it never decides
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

**`benchmarks/`**, the pages assay is scored on:

- `generated/` holds the programs an AI wrote, with their answer keys.
- `planted/` holds the working programs and the copies with planted bugs.
- `harness/` holds the two scorers and the answer key for grouped findings.

**`tests/`** is the test suite. **`docs/`** holds the docs and the scripts
that draw the README's pictures from real runs.

---

## Changing a rule

A rule is anything that decides whether a check failed. Most live in `judge`
in `run.py`, and the checks that exercise them are built in `surface.py`.

1. **Write two tests.** One is a page the rule should flag, and the other is
   a page it must not flag. Pure comparisons go in `tests/test_judge.py`,
   which needs no browser. Anything needing a real page goes in
   `tests/test_end_to_end.py`.
2. **Run both benchmarks** and put the before and after numbers in the pull
   request. The tests can't see a false alarm on a working program, but the
   benchmarks can.
3. **A false alarm costs more than a miss.** A rule that catches three more
   bugs but flags one working page is not an improvement, because a false
   alarm sends someone to change code that was right.
4. **Say what happened, in plain words.** A message says what assay did and
   what the page did in response, like *when pressed twice from the same
   starting point, this changed nothing on the first press and changed the
   page on the second, so it reacts one press late*. It never gives a bare
   verdict like *this page is broken*, and it should make sense to someone
   who hasn't read the rule.
5. **Document it.** Add the rule to `docs/how-it-works.md` under the action
   that triggers it, with what assay does, the message it prints, and when it
   stays quiet and why.

A fix for a false alarm needs the page that was flagged, added as a test that
must stay clean.

---

## Tests

```bash
pytest -q
```

The full suite takes about 25 minutes, because most tests drive a real
browser. `tests/test_judge.py`, `tests/test_plan.py`, `tests/test_links.py`,
`tests/test_perform.py` and `tests/test_translations.py` need no browser and
run in seconds, so run those while you work. `tests/test_end_to_end.py` takes
most of the time, and skips rather than fails when there's no browser.

CI runs the whole suite on Python 3.10, 3.11, 3.12, 3.13 and 3.14 for every
pull request, plus a short run of both benchmark scorers. All of it must pass
before anything is merged.

A bug fix needs a test that fails before the fix and passes after.

---

## Benchmarks

```bash
python benchmarks/harness/generated.py    # the generated set
python benchmarks/harness/planted.py      # the planted set
```

A change to a rule or to `benchmarks/` needs both scorers run before and
after the change. Each prints a summary line, and both lines go in the pull
request. A change counts as an improvement only when it finds more bugs
without flagging a page that works.

The judgements in the answer keys are written by hand. If your change makes
assay report something new on a benchmark program, the scorer writes nothing
until you record what the new finding is.

[Harness](../benchmarks/harness/README.md)

---

## Adding a harness

- **If the harness reads skills,** add its install steps to
  `docs/harnesses.md`, pointing at `plugins/assay/skills/checking-a-page/`.
- **If it has its own plugin format,** add its marketplace file next to the
  others (`.claude-plugin/`, `.cursor-plugin/`, `.grok-plugin/`,
  `.agents/plugins/`, `.github/plugin/`) and document it in the same place.
- **Test it in the harness** and say which version you used.
- **Update the count.** The README, the install page, the harness page and
  the plugin's README all say how many harnesses are supported.
- **It reports and never fixes.** The skill and plugin pass on what was
  pressed and what happened, and don't edit code because of it. Keep it that
  way.

---

## Changing the docs

The docs are also kept in Simplified Chinese, Japanese, Korean and Russian.
Change only the English. `tests/test_translations.py` then fails, which is
expected, and a maintainer updates the translations before the change is
merged.

---

## Docs

| Doc | What it covers |
|---|---|
| [Translating the docs](development/translating.md) | The convention every translation follows, and how the test keeps translations current |
| [Glossary](development/glossary.md) | The word each language uses for assay's terms |
