# Contributing

Issues and pull requests are welcome. Fork, branch, open a PR.

## Contents

- [Setup](#setup)
- [Tests](#tests)
- [Benchmarks](#benchmarks)
- [What a PR Needs](#what-a-pr-needs)
- [What Makes a Good Issue](#what-makes-a-good-issue)

## Setup

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
python -m playwright install chromium
```

## Tests

```bash
pytest -q
```

About twenty minutes, because most of it drives a real browser. CI runs the
suite on every pull request, so run it locally when you change `src/` and
skip it when you change docs.

## Benchmarks

```bash
python bench/score.py            # 225 generated programs, about 75 minutes
python bench/planted/score.py    # 50 planted bugs, about eight minutes
```

Neither needs a key or a network, and neither is required for most PRs. CI
runs a three-program smoke test so the scorer cannot silently break.

## What a PR Needs

- Tests for what it changes.
- If it adds or changes a **rule**, two tests: a page it should flag and a
  page it must not. Then run both benchmarks and put the numbers in the PR.
  The suite cannot see a false alarm on a working program; the benchmarks
  can, and a false alarm costs more than a miss.

## What Makes a Good Issue

A false alarm: a page that works and assay flagged. It has never happened on
the benchmarks and it costs more than anything else assay can do, because it
sends someone off to fix code that was right. Attach the page.

A bug: a crash, a hang, a wrong count, a control it should have driven and
did not.

An improvement: anything that moves the benchmark numbers, or makes the
check faster or the output clearer. Run both benchmarks and put the numbers
in the PR.

A miss is not an issue. assay finds a fraction of what is broken, by design.
It is a quick, cheap, mechanical check, and a page it called clean that
turned out to be broken is the expected case, not a bug.
