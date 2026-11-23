<!-- i18n-source: docs/getting-started.md 87f5daae1ec1d0ee044476575debceac6d4328a6 -->

<h1 align="center">快速上手</h1>

<p align="center"><a href="../README.zh-CN.md">assay</a> › 快速上手</p>

<p align="center"><a href="getting-started.md">English</a> · <b>简体中文</b> · <a href="getting-started.ja.md">日本語</a> · <a href="getting-started.ko.md">한국어</a> · <a href="getting-started.ru.md">Русский</a></p>

<p align="center">从安装 assay 到日常使用。</p>

---

## <a id="contents"></a>目录

- [开始之前](#before-you-start)
- [检查页面](#checking-a-page)
- [读懂结果](#reading-the-result)
- [有 bug 的页面](#a-page-with-a-bug)
- [选择页面](#choosing-the-page)
- [HTML 报告](#the-html-report)
- [简短摘要](#a-short-summary)
- [配合编程智能体使用](#with-a-coding-agent)
- [接下来看什么](#where-to-go-next)

---

## <a id="before-you-start"></a>开始之前

你需要 Python 3.10 或更高版本，以及一个浏览器能打开的页面，也就是一个包含 `.html` 文件的文件夹。

```bash
pip install assay-ui
```

如果你的项目有构建步骤，请先构建，再检查输出文件夹。assay 从不自己运行构建。

[全部安装方式](install.zh-CN.md)

---

## <a id="checking-a-page"></a>检查页面

把 assay 指向存放页面的文件夹。

```console
assay ./my-app
```

首次运行会下载 Chromium，这只发生一次。之后 assay 会在 localhost 上托管这个文件夹，在 Chromium 中打开 `index.html`，列出页面渲染出的每个控件（control），根据这些控件规划检查（check），并在新的标签页中运行每项检查。大多数页面需要几秒到一分钟。

仓库中存放着用于给 assay 评分的页面，所以在仓库的克隆中可以直接运行本页的示例。下面这个是一个能正常工作的点击计数器。

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter
7 cases planned, 7 carried out, 7 passed, 0 failed

C001 [ok] open the page and let it settle
C002 [ok] press Increment
C003 [ok] press Increment twice
C004 [ok] press Reset
C005 [ok] press Reset twice
C006 [ok] press Increment, then Reset
C007 [ok] press Reset, then Increment
```

---

## <a id="reading-the-result"></a>读懂结果

第一行统计 assay 规划了多少项检查、其中多少项得以执行，以及多少项通过、多少项失败。之后的每一行是一项检查，包含它的编号、结果和它做了什么。

| 结果 | 含义 |
|---|---|
| `[ok]` | 检查已运行，没有发现问题 |
| `[FAILED]` | 页面自相矛盾（the page contradicts itself），检查下面的那一行说明了具体情况 |
| `[not checked]` | assay 无法执行这项检查，这种情况从不算作失败 |

没有检查失败时退出码为 0，有检查失败时为 1，页面完全无法检查时为 2，脚本可以据此处理。

除了首次运行时下载 Chromium 以外，assay 只在你要求时才向磁盘写入内容。

---

## <a id="a-page-with-a-bug"></a>有 bug 的页面

下面这个是一个小型绘图程序，它的 Undo 总是晚一次才有反应。

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

C016 就是失败的那项检查。第一次 Undo 什么也没做，第二次才完成撤销，所以 Undo 落后了一次。

当一个 bug 导致多项检查失败时，第一项失败会显示消息，其余的则指回第一项，所以这条消息你只需要读一次。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

assay 不知道你的页面是做什么用的，所以一个问题（finding）只是值得查看的地方，而不是已确认的 bug。一个控件在被按下时所处的状态下什么都不做，也可能是正确的。

---

## <a id="choosing-the-page"></a>选择页面

```console
assay ./my-app                    # 检查该文件夹中的 index.html
assay ./my-app/todo.html          # 检查指定的页面
assay ./my-app -e app.html        # 或者指定文件夹中的某个页面
```

assay 一次检查一个页面，页面由本地文件夹托管。如果你把它指向需要构建的源码目录，它会告诉你该运行什么。

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

## <a id="the-html-report"></a>HTML 报告

`--report` 会生成一个可以直接打开的页面，展示每项检查前后的页面。

```console
assay ./my-app --report out.html
```

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="assay 报告中的一项检查，检查对象是一个标签筛选器。标签被点击两次后外观恢复原样，但列表仍处于筛选状态。图中列出了操作步骤、原因，以及检查前后的页面截图，列表从十二项变成了一项。">

报告是一个 HTML 文件，截图放在它旁边一个以报告命名的文件夹中，这里是 `out-shots`。

---

## <a id="a-short-summary"></a>简短摘要

`--one-line` 会输出简短摘要，供脚本和智能体（agent）读取。

```console
$ assay ./todo --one-line
assay: checked todo/index.html, 8 checks, nothing flagged.
```

发现问题时，摘要会列出每个问题，重复的问题会指明第一个问题，而不会重复它的消息。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

---

## <a id="with-a-coding-agent"></a>配合编程智能体使用

assay 为编程智能体（coding agent）提供了两样东西。

**skill** 让你的智能体在写完页面后运行 assay，并在回复末尾附上结果。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**插件**（plugin）会添加一个钩子（hook），在每一轮（turn）修改了页面的对话结束时自动运行检查。在 Claude Code 中，下面两条命令会同时安装 skill 和钩子。

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

无论使用哪种方式，智能体都会报告 assay 发现的问题，除非你要求，否则不会因此修改代码。

[Harness](harnesses.zh-CN.md) · [skill 与插件](../plugins/assay/README.zh-CN.md)

---

## <a id="where-to-go-next"></a>接下来看什么

文档涵盖每个选项和 Python API、assay 所做的每项检查及其输出的消息，以及每种编程智能体 harness（智能体运行框架）的设置方法。

[文档](../README.zh-CN.md#docs)

---

本文是 [getting-started.md](getting-started.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
