<!-- i18n-source: docs/harnesses.md 754a27f7ad6e3db62fad6db5ec61f13ed63618f1 -->

<h1 align="center">在你的 harness 中安装 assay</h1>

<p align="center"><a href="harnesses.md">English</a> · <b>简体中文</b> · <a href="harnesses.ja.md">日本語</a> · <a href="harnesses.ko.md">한국어</a> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">15 种 harness（智能体运行框架）的安装步骤。其中 8 种可以用各自的插件（plugin）命令安装 assay。其余 7 种需要你把 skill 文件复制到相应位置，这种做法适用于任何能读取 skill 的 harness。</p>

---

## <a id="contents"></a>目录

- [你会得到什么](#what-you-get)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Grok Build CLI](#grok-build-cli)
- [Cursor](#cursor)
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

通过插件安装，两者都会装上，只有 Cursor 例外，在 Cursor 中插件只安装 skill。在 Claude Code、Codex、Grok Build CLI、Devin CLI、Factory Droid、GitHub Copilot CLI 和 DeepSeek Harness 中，每一轮（turn）只要修改了页面，钩子就会在这一轮结束时运行检查。DeepSeek Harness 以复制文件的方式获得 skill，并通过它的 Claude Code 桥接使用钩子。opencode 和[其他 harness](#everywhere-else-the-skill-on-its-own) 一节中的 harness 只安装 skill，在这些 harness 中，智能体按照 skill 的指示自行运行检查。

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

## <a id="codex"></a>Codex

在 Codex CLI 中，添加插件市场（marketplace）并安装插件。

```bash
codex plugin marketplace add awss1i/assay
codex plugin add assay@assay
```

然后开启一个新会话，打开 `/hooks`，并信任 assay 的钩子。在你信任插件的钩子之前，Codex 会跳过它，所以如果不做这一步，你只会得到 skill。更新时运行 `codex plugin marketplace upgrade assay`。

Codex App 是 ChatGPT 桌面应用中的 Codex。在 Codex App 中，先运行上面的 `codex plugin marketplace add` 命令，然后重启应用，再在 Plugins（插件）中找到 assay 插件市场并安装 assay。

---

## <a id="grok-build-cli"></a>Grok Build CLI

```bash
grok plugin marketplace add awss1i/assay
grok plugin install assay --trust
```

如果不加 `--trust`，Grok 不会安装带有钩子的插件。它会停下来，让你加上 `--trust` 重新运行这条命令。安装成功后，`grok inspect` 会列出 `checking-a-page` skill 和这个钩子。更新时先运行 `grok plugin marketplace update`，再运行 `grok plugin update assay`。

---

## <a id="cursor"></a>Cursor

在编辑器中（需要 Cursor 2.5 及以上版本），在 Agent 聊天中输入以下内容。

```
/add-plugin assay@https://github.com/awss1i/assay
```

在 Cursor CLI 中，先添加插件市场，然后在会话中通过 `/plugin` 安装 assay。

```bash
agent plugin marketplace add https://github.com/awss1i/assay
```

无论用哪种方式，你都会得到 skill。在 Cursor 中，插件不会添加钩子，因为 Cursor 的钩子使用不同的格式。如果想改为单独安装 skill，可以使用 skills CLI。

```bash
npx skills add awss1i/assay --agent cursor       # 当前项目，安装到 .agents/skills/
npx skills add awss1i/assay --agent cursor -g    # 所有项目，安装到 ~/.agents/skills/
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh 会读取项目中 `.agents/skills/` 里的 skill，以及对所有项目生效的 `~/.agents/skills/` 里的 skill，但不会读取 `.claude/skills/`。把 skill 复制到其中一个文件夹。

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

dsh 的默认权限模式会阻止命令写入项目以外的位置，而第一次检查会把 Chromium 下载到你的主目录，所以 dsh 可能会请你批准一次。如果想避免这个提示，可以在你自己的 shell 中运行第一次检查。

至于钩子，dsh 通过自带的桥接运行 Claude Code 的钩子配置。没有任何 profile 自带这个桥接，所以要在 `$DSH_HOME/cordis.patch.yml` 中添加它。这个文件会在每个 profile 自己的配置层之后应用，因此对 `web`、`headless` 以及你创建的任何 profile 都生效。

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
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

opencode 会读取 `.agents/skills/`、`.opencode/skills/`、`.claude/skills/` 和 `~/.config/opencode/skills/`。建议使用 `.agents/skills/`，因为 DeepSeek Harness、Cursor 和 Hermes Agent 也会读取它，一个文件夹就能同时供这四者使用。

---

## <a id="devin-cli"></a>Devin CLI

只有在你登录后，Devin 才能管理插件，所以请先运行 `devin auth login`。

```bash
devin plugins install awss1i/assay#plugins/assay
```

插件位于 `plugins/assay`，`#` 用来告诉 Devin 去那里查找。加上 `--local` 可以只把插件安装在这台机器上，而不是安装到你的 Devin Cloud 清单（manifest）中。更新时运行 `devin plugins update assay`。Devin 会尽量运行插件的钩子，但不保证一定运行，钩子运行失败也不会中断这一轮。

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

在交互式的 Droid 中，钩子只会在你信任过的文件夹中运行。

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

Copilot 会直接把钩子的报告展示给你，而不是传给智能体。你会在终端中看到这份报告，它位于发给智能体的那一行下方，智能体不会再重复它。

---

## <a id="everywhere-else-the-skill-on-its-own"></a>在其他 harness 中单独使用 skill

*Antigravity、Gemini CLI、Kimi Code、Pi、Hermes Agent。*

assay 没有提供这些 harness 格式的插件，所以要以文件的形式安装 skill。它只是一个 markdown 文件，在任何能读取 skill 或指令文件的地方都能使用。

把 [`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page) 复制到你的 harness 读取 skill 的文件夹，例如项目中的 `.agents/skills/`（Hermes Agent 会读取这个文件夹），或者把这个文件的内容粘贴到你的 `AGENTS.md` 中。

没有钩子时，检查不会在每一轮结束时自动运行，而是由智能体决定何时运行。

**[skill 的工作方式 →](../plugins/assay/README.zh-CN.md#the-skill)**

---

本文是 [harnesses.md](harnesses.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
