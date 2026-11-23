<h1 align="center">Install</h1>

<p align="center"><a href="../README.md">assay</a> › Install</p>

<p align="center"><b>English</b> · <a href="install.zh-CN.md">简体中文</a> · <a href="install.ja.md">日本語</a> · <a href="install.ko.md">한국어</a> · <a href="install.ru.md">Русский</a></p>

<p align="center">Every way to install assay.</p>

---

## Contents

- [pip](#pip)
- [uv](#uv)
- [pipx](#pipx)
- [Chromium](#chromium)
- [Updating](#updating)
- [Uninstalling](#uninstalling)
- [Coding agents](#coding-agents)

---

## pip

```bash
pip install assay-ui
```

assay needs Python 3.10 or newer. The package is called `assay-ui`, and the
command it installs is `assay`. If `pip` isn't found, use
`python3 -m pip install assay-ui`.

---

## uv

```bash
uv tool install assay-ui
```

uv downloads a Python for assay when the system has none at 3.10 or newer,
and puts the `assay` command on your `PATH`.

---

## pipx

```bash
pipx install assay-ui
```

pipx installs assay in its own isolated environment, apart from your other
Python packages.

---

## Chromium

assay opens pages in Chromium, through Playwright. The first run checks
whether Chromium is installed, and downloads it when it isn't. Before the
download starts, assay prints this.

```
assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.
```

With a pip install, you can download Chromium ahead of time, for example
while building a container image.

```bash
python -m playwright install chromium
```

On Linux, Chromium needs some system libraries. If the first run fails
because one is missing, this command installs them along with Chromium.

```bash
python -m playwright install --with-deps chromium
```

---

## Updating

| Installed with | Command |
|---|---|
| pip | `pip install --upgrade assay-ui` |
| uv | `uv tool upgrade assay-ui` |
| pipx | `pipx upgrade assay-ui` |

`assay --version` prints the installed version.

---

## Uninstalling

| Installed with | Command |
|---|---|
| pip | `pip uninstall assay-ui` |
| uv | `uv tool uninstall assay-ui` |
| pipx | `pipx uninstall assay-ui` |

Uninstalling assay leaves Chromium in Playwright's cache. With a pip install,
run `python -m playwright uninstall` before you uninstall assay, and
Playwright removes the browsers it downloaded.

---

## Coding agents

The skill and the plugin both run the `assay` command, so install assay with
one of the commands above first. Each harness then has its own steps.

| Harness | What it installs |
|---|---|
| [Claude Code](harnesses.md#claude-code) | The skill and the hook, as a plugin |
| [Codex](harnesses.md#codex) | The skill and the hook, as a plugin |
| [Grok Build CLI](harnesses.md#grok-build-cli) | The skill and the hook, as a plugin |
| [Cursor](harnesses.md#cursor) | The skill, as a plugin |
| [DeepSeek Harness](harnesses.md#deepseek-harness) | The skill as a copied file, and the hook through its Claude Code bridge |
| [opencode](harnesses.md#opencode) | The skill, as a copied file |
| [Devin CLI](harnesses.md#devin-cli) | The skill and the hook, as a plugin |
| [Factory Droid](harnesses.md#factory-droid) | The skill and the hook, as a plugin |
| [GitHub Copilot CLI](harnesses.md#github-copilot-cli) | The skill and the hook, as a plugin |
| [Antigravity, Gemini CLI, Kimi Code, Pi and Hermes Agent](harnesses.md#everywhere-else-the-skill-on-its-own) | The skill, as a copied file |
