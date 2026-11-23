<h1 align="center">Contributing</h1>

<p align="center"><a href="README.md">assay</a> › Contributing</p>

<p align="center">Where bugs, questions and changes go, and what a pull request needs.</p>

---

## Contents

- [Where things go](#where-things-go)
- [Titles](#titles)
- [Pull requests](#pull-requests)
- [Bugs](#bugs)
- [Setup](#setup)

---

## Where things go

Bugs go in issues, questions and ideas go in Discussions, and fixes and
features come as pull requests.

| Where | What goes there |
|---|---|
| Issues | Bugs, problems in the docs, and anything else that's wrong |
| Discussions | Questions and ideas |
| Pull requests | Fixes, features and misc changes |

A working page that assay flagged is a bug, and so is a crash, a hang or a
wrong count. A broken page that assay called clean is a miss, and teaching
assay to catch it comes as a pull request. A security problem is reported
privately.

AI assistance is welcome. Keep pull requests and issues short, and cut anything that doesn't help a maintainer understand the change.

[Discussions](https://github.com/awss1i/assay/discussions) · [Security](SECURITY.md)

---

## Titles

The title of a pull request or a bug starts with the area it touches, then a
colon, then what changed in lowercase.

```
cli: keep page text in --one-line on one line
```

| Area | What it covers |
|---|---|
| `checks` | Finding the controls, planning the checks, running them and deciding what failed |
| `cli` | The `assay` command and what it prints |
| `report` | The HTML report |
| `plugin` | The skill, the plugin's hook and the harness manifests |
| `benchmarks` | The benchmark pages, their answer keys and the scorers |
| `docs` | The README and the docs |
| `ci` | The workflows, the templates and the labels |
| `deps` | Dependencies |

Each area has a label, and a workflow labels a pull request from the files
it changes. A check fails a pull request whose title doesn't start with an
area.

---

## Pull requests

A pull request makes one change, and its description follows this template.

```markdown
## The change

What changed and why, in a few sentences.

## Tests

What the test checks and why, or N/A.

---

- [ ] Fix
- [ ] Feature
- [ ] Misc
- [ ] I used AI assistance (maintainers can skip this)
```

Misc covers everything that isn't a fix or a feature, such as docs, CI and
dependencies. A fix needs a test that fails before it and passes after, and a
change to a rule needs both benchmarks run before and after.

[Development](docs/development.md)

---

## Bugs

The bug form has three fields.

| Field | What to write |
|---|---|
| What happened | What you expected, and what you got instead. For a working page that assay flagged, say why the page is right |
| How to reproduce | The command you ran, what assay printed, and the smallest page that shows it, attached or linked |
| Version | The output of `assay --version` |

---

## Setup

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
python -m playwright install chromium
```

Use the editable install. If `assay-ui` from PyPI is installed in the same
Python, it's imported instead of your clone and the tests run against the
release. Check with `python -c "import assay; print(assay.__file__)"`. It
should point into this folder.

```bash
pytest -q
```

The full suite takes about 25 minutes, because most tests drive a real
browser. `tests/test_judge.py`, `tests/test_plan.py`, `tests/test_links.py`,
`tests/test_perform.py` and `tests/test_translations.py` need no browser and
run in seconds.
