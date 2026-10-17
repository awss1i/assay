<!-- i18n-source: plugins/assay/README.md 180af1a6b8d06f59dee6add968b42fecd831ed93 -->

<h1 align="center">skill 与插件</h1>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

---

<p align="center">让智能体（agent）检查它刚写好的页面，有两种方式。<strong><a href="../../docs/harnesses.zh-CN.md">15 种 harness（智能体运行框架）的安装步骤 →</a></strong></p>

---

## <a id="contents"></a>目录

- [skill](#the-skill)
- [插件](#the-plugin)
- [只报告，不修复](#reporting-not-fixing)

---

## <a id="the-skill"></a>skill

skill 可在全部 15 种受支持的 harness 中使用。[`skills/checking-a-page/SKILL.md`](skills/checking-a-page/SKILL.md) 让智能体在写完页面后运行这条命令。

```bash
assay <the page> --one-line
```

然后在回复末尾逐字附上命令的输出。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

如果发现了问题，输出是这样的。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

这四行其实是同一个 bug。重复的几行不再重复消息，而是指明第一个问题（finding）。智能体会原样复制 assay 的输出，而不是自己总结，所以数字和措辞都保持准确。如果只安装 skill，由智能体决定何时运行检查（check）。

---

## <a id="the-plugin"></a>插件

插件（plugin）会添加一个 `Stop` 钩子（hook），在每一轮（turn）修改了页面的对话结束时运行检查。在 Claude Code、Codex、Grok Build CLI、Devin CLI、Factory Droid 和 GitHub Copilot CLI 中，插件会同时安装 skill 和钩子。在 Cursor 中，插件只安装 skill。DeepSeek Harness 通过它的 Claude Code 桥接运行这个钩子。

- **检查哪些页面。** 任何网页文件发生变化，都会标记同一文件夹中的页面，所以修改 `app.js` 也算。在每个文件夹中，钩子会检查最近修改的 `.html` 文件，修改时间相同时优先选择 `index.html`。
- **查找范围。** 钩子最多向下搜索四层文件夹，跳过 `node_modules` 和 `.git`，只考虑上次运行之后修改过的文件，每一轮最多检查三个页面。
- **只要检查了页面就一定会报告**，这样没有问题的结果就不会被误认为是 assay 没有运行。没有修改任何页面的一轮不会报告任何内容。
- **暂不结束这一轮**，好让你看到结果，但不会连续两次这样做。钩子会检查 harness 的 `stop_hook_active` 标志，并写入一个时间戳（写在 harness 的临时文件夹中，没有的话写在仓库的 `.git` 文件夹中，再没有的话写入 `.assay-last-run` 文件）。如果无法写入时间戳，钩子会照常报告，但不会阻止这一轮结束。
- **按时结束。** 钩子给每个页面最多四分钟，给所有页面合计最多九分钟，这样它会在 harness 按照 `hooks.json` 中设定的十分钟上限取消它之前结束。没来得及检查的页面会被报告为未检查（not checked）。

---

## <a id="reporting-not-fixing"></a>只报告，不修复

智能体会把 assay 发现的问题展示给你，除非你要求，否则不会因此修改代码。assay 不知道页面是做什么用的，所以每个问题只是一个值得查看的地方，而不是已经确认的 bug。一个控件（control）在被按下时所处的状态下什么都不做，可能本来就是正确的，一个数值也可能是有意限制的。如果你让智能体修复某个问题，它就会去修复。

---

本文是 [README.md](README.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
