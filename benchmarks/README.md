<h1 align="center">Benchmarks</h1>

<p align="center"><a href="../README.md">assay</a> › Benchmarks</p>

<p align="center"><strong>How many real bugs assay finds, and how many working pages it flags, on two sets of pages kept in this repository.</strong></p>

---

## Contents

- [Results](#results)
- [The two sets](#the-two-sets)
- [How a page is scored](#how-a-page-is-scored)
- [Running them yourself](#running-them-yourself)
- [Docs](#docs)

---

## Results

<!-- results -->

| Set | Pages | Bugs found | Working pages flagged |
|---|---|---|---|
| [Pages written by AI](generated.md) | 225 | 15 of 20 | 0 of 205 |
| [Pages with planted bugs](planted.md) | 20 | 12 of 50 | 0 of 10 |

On the pages written by AI, the median page took 14 seconds to check, and 221 of the 225 finished inside a minute.

<!-- /results -->

The scoring scripts write this table and each set's doc from their own runs.
Bugs found counts the bugs assay flagged out of the bugs the set has. Working
pages flagged counts the pages that work and that assay flagged anyway, which
are its false alarms.

---

## The two sets

**Pages written by AI.** These are small web apps that several coding
harnesses wrote on one model from the same list of objectives. A person
opened and used every one, and recorded whether it works and what is wrong
when it doesn't. Most of them work, so this set mainly shows whether assay
leaves working pages alone, and it only covers the bugs the programs happened
to have.

**Pages with planted bugs.** This set starts from programs that work and
plants bugs in a copy of each, so assay is measured against a known list of
bugs. One harness and model wrote the programs, and a different harness and
model planted the bugs. Neither was told assay exists. assay's rules were
developed with this set in view, so its score is in-sample.

---

## How a page is scored

- **A bug counts as found only when assay flagged that bug.** A flag for
  something else on the same page doesn't count. Deciding which flag is the
  bug takes judgement, so a person writes it down in the set's answer key.
- **A working page that assay flags is a false alarm.** Misses and false
  alarms are counted separately because a false alarm costs more. It sends
  someone to change code that was right.
- **There's no single accuracy percentage.** Most pages in the generated set
  work, so a tool that called every page clean without opening a browser
  would agree with the answer key most of the time.
- **Only a complete run is published.** A scorer writes nothing while any
  flag on a broken page has no verdict, so the numbers always come from a
  run in which every flag was judged.

---

## Running them yourself

```bash
pip install -e .
python -m playwright install chromium
python benchmarks/harness/generated.py
python benchmarks/harness/planted.py
```

Neither script needs an API key or network, because the pages are in the
repository and assay runs them in a local browser.

[Harness](harness/README.md)

---

## Docs

| Doc | What it covers |
|---|---|
| [The generated set](generated.md) | Every broken program an AI wrote, what is wrong with it, and whether assay found it |
| [The planted set](planted.md) | Every planted bug, and the finding that showed it or why assay missed it |
