<!-- i18n-source: docs/harnesses.md 35ce1703961c0b049eb853466b5b884081a86ff7 -->

<h1 align="center">在你的 harness 中安装 assay</h1>

<p align="center"><a href="harnesses.md">English</a> · <b>简体中文</b> · <a href="harnesses.ja.md">日本語</a> · <a href="harnesses.ko.md">한국어</a> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">15 种 harness（智能体运行框架）的安装步骤。其中 6 种可以用各自的插件（plugin）命令安装 assay。其余 9 种需要你把 skill 文件复制到相应位置，这种做法适用于任何能读取 skill 的 harness。</p>

---

## <a id="contents"></a>目录

- [你会得到什么](#what-you-get)
- [Claude Code](#claude-code)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [在其他 harness 中单独使用 skill](#everywhere-else-the-skill-on-its-own)

---

## <a id="what-you-get"></a>你会得到什么

assay 由两部分组成：

- 一个 **skill**，它让你的智能体（agent）在写完页面后运行 `assay`，并把结果展示给你，以及
- 一个**钩子（hook）**，它会自动运行检查（check）。

通过插件安装，两者都会装上。钩子适用于 Claude Code 和 DeepSeek Harness，在这两者中，每一轮（turn）只要修改了页面，结束时就会运行检查。在其他 harness 中，智能体按照 skill 的指示自行运行检查。opencode 和[其他 harness](#everywhere-else-the-skill-on-its-own) 一节中的 harness 只安装 skill，而 DeepSeek Harness 只使用钩子，通过它的 Claude Code 桥接来运行。

这 15 种 harness 都需要先确保 `assay` 位于你的 `PATH` 中。

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # 没有 Python 3.10+ 时由 uv 下载一个
```

```bash
pipx install assay-ui          # 把 assay 安装在单独的隔离环境中
```

---

## <a id="claude-code"></a>Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh 通过自带的桥接运行 Claude Code 的钩子配置。没有任何 profile 自带这个桥接，所以要在 `$DSH_HOME/cordis.patch.yml` 中添加它。这个文件会在每个 profile 自己的配置层之后应用，因此对 `web`、`headless` 以及你创建的任何 profile 都生效。

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: /abs/path/to/assay/plugins/assay/hooks/hooks.json
        pluginRoot: /abs/path/to/assay/plugins/assay
```

如果你没有设置 `$DSH_HOME`，它默认是 `~/.dsh`。两个路径都使用绝对路径，因为钩子运行时有自己的工作目录。`dsh --dump-config` 会输出合成后的配置树，可以用它确认桥接是否已经挂载。

如果只想让它对某一个 profile 生效，可以改为把同样的配置块放进该 profile 的 `cordis.patch.yml`，或者在每次运行时通过 `--patch` 传入。

---

## <a id="opencode"></a>opencode

```bash
mkdir -p .claude/skills
cp -r plugins/assay/skills/checking-a-page .claude/skills/
```

opencode 会读取 `.claude/skills/`、`.opencode/skills/`、`.agents/skills/` 和 `~/.config/opencode/skills/`。建议使用 `.claude/skills/`，因为 Claude Code 也会读取它，一个文件夹就能同时供两者使用。

---

## <a id="devin-cli"></a>Devin CLI

```bash
devin plugins install awss1i/assay#plugins/assay
```

插件位于 `plugins/assay`，`#` 用来告诉 Devin 去那里查找。更新时运行 `devin plugins update assay`。

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

---

## <a id="everywhere-else-the-skill-on-its-own"></a>在其他 harness 中单独使用 skill

*Antigravity、Codex App、Codex CLI、Cursor、Gemini CLI、Grok Build CLI、Kimi Code、Pi、Hermes Agent。*

assay 没有提供这些 harness 格式的插件，所以要以文件的形式安装 skill。它只是一个 markdown 文件，在任何能读取 skill 或指令文件的地方都能使用。

把 [`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page) 复制到你的 harness 读取 skill 的文件夹，例如项目中的 `.agents/skills/`（Hermes Agent 会读取这个文件夹），或者把这个文件的内容粘贴到你的 `AGENTS.md` 中。

没有钩子时，检查不会在每一轮结束时自动运行，而是由智能体决定何时运行。

**[skill 的工作方式 →](../plugins/assay/README.zh-CN.md#the-skill)**

---

本文是 [harnesses.md](harnesses.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
