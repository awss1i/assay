<!-- i18n-source: docs/install.md c51339dcc8b0355b209153fdf0186ea21a55095f -->

<h1 align="center">安装</h1>

<p align="center"><a href="../README.zh-CN.md">assay</a> › 安装</p>

<p align="center"><a href="install.md">English</a> · <b>简体中文</b> · <a href="install.ja.md">日本語</a> · <a href="install.ko.md">한국어</a> · <a href="install.ru.md">Русский</a></p>

<p align="center">安装 assay 的所有方式。</p>

---

## <a id="contents"></a>目录

- [pip](#pip)
- [uv](#uv)
- [pipx](#pipx)
- [Chromium](#chromium)
- [更新](#updating)
- [卸载](#uninstalling)
- [编程智能体](#coding-agents)

---

## <a id="pip"></a>pip

```bash
pip install assay-ui
```

assay 需要 Python 3.10 或更高版本。软件包名为 `assay-ui`，它安装的命令是 `assay`。如果找不到 `pip`，请改用 `python3 -m pip install assay-ui`。

---

## <a id="uv"></a>uv

```bash
uv tool install assay-ui
```

当系统中没有 3.10 或更高版本的 Python 时，uv 会为 assay 下载一个，并把 `assay` 命令放到你的 `PATH` 中。

---

## <a id="pipx"></a>pipx

```bash
pipx install assay-ui
```

pipx 会把 assay 安装在单独的隔离环境中，与你的其他 Python 软件包分开。

---

## <a id="chromium"></a>Chromium

assay 通过 Playwright 在 Chromium 中打开页面。首次运行时，assay 会检查 Chromium 是否已安装，没有安装就下载。开始下载之前，assay 会输出下面这行。

```
assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.
```

用 pip 安装时，可以提前下载 Chromium，例如在构建容器镜像的时候。

```bash
python -m playwright install chromium
```

在 Linux 上，Chromium 需要一些系统库。如果首次运行因为缺少某个库而失败，下面这条命令会把这些库和 Chromium 一起安装。

```bash
python -m playwright install --with-deps chromium
```

---

## <a id="updating"></a>更新

| 安装方式 | 命令 |
|---|---|
| pip | `pip install --upgrade assay-ui` |
| uv | `uv tool upgrade assay-ui` |
| pipx | `pipx upgrade assay-ui` |

`assay --version` 会输出已安装的版本。

---

## <a id="uninstalling"></a>卸载

| 安装方式 | 命令 |
|---|---|
| pip | `pip uninstall assay-ui` |
| uv | `uv tool uninstall assay-ui` |
| pipx | `pipx uninstall assay-ui` |

卸载 assay 后，Chromium 仍留在 Playwright 的缓存中。用 pip 安装时，先运行 `python -m playwright uninstall` 再卸载 assay，Playwright 就会删除它下载的浏览器。

---

## <a id="coding-agents"></a>编程智能体

skill 和插件（plugin）都要运行 `assay` 命令，所以请先用上面的某条命令安装 assay。之后每种 harness（智能体运行框架）有各自的步骤。

| Harness | 安装的内容 |
|---|---|
| [Claude Code](harnesses.zh-CN.md#claude-code) | skill 和钩子（hook），以插件形式安装 |
| [Codex](harnesses.zh-CN.md#codex) | skill 和钩子（hook），以插件形式安装 |
| [Grok Build CLI](harnesses.zh-CN.md#grok-build-cli) | skill 和钩子（hook），以插件形式安装 |
| [Cursor](harnesses.zh-CN.md#cursor) | skill，以插件形式安装 |
| [DeepSeek Harness](harnesses.zh-CN.md#deepseek-harness) | 以复制文件的方式安装 skill，钩子通过它的 Claude Code 桥接运行 |
| [opencode](harnesses.zh-CN.md#opencode) | skill，以复制文件的方式安装 |
| [Devin CLI](harnesses.zh-CN.md#devin-cli) | skill 和钩子（hook），以插件形式安装 |
| [Factory Droid](harnesses.zh-CN.md#factory-droid) | skill 和钩子（hook），以插件形式安装 |
| [GitHub Copilot CLI](harnesses.zh-CN.md#github-copilot-cli) | skill 和钩子（hook），以插件形式安装 |
| [Antigravity、Gemini CLI、Kimi Code、Pi 和 Hermes Agent](harnesses.zh-CN.md#everywhere-else-the-skill-on-its-own) | skill，以复制文件的方式安装 |

---

本文是 [install.md](install.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
