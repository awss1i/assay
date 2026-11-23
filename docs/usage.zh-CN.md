<!-- i18n-source: docs/usage.md 4fc8af90f6d6d12babc4d55ec7e9668ec62ae3d8 -->

<h1 align="center">使用</h1>

<p align="center"><a href="../README.zh-CN.md">assay</a> › 使用</p>

<p align="center"><a href="usage.md">English</a> · <b>简体中文</b> · <a href="usage.ja.md">日本語</a> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>

<p align="center">assay 命令的每个选项、它的输出、退出码、HTML 报告和 Python API。</p>

---

## <a id="contents"></a>目录

- [命令](#the-command)
- [选项](#options)
- [assay 的输出](#what-assay-prints)
  - [默认输出](#the-default-output)
  - [简短摘要](#the-short-summary)
  - [JSON](#json)
  - [控件列表](#the-controls)
- [退出码](#exit-codes)
- [HTML 报告](#the-html-report)
- [颜色](#colour)
- [错误](#errors)
- [在 Python 中使用](#from-python)
  - [检查页面](#checking-a-page)
  - [验收标准](#acceptance-criteria)
  - [列出控件](#listing-the-controls)

---

## <a id="the-command"></a>命令

```console
assay ./my-app                    # 检查该文件夹中的 index.html
assay ./my-app/todo.html          # 检查指定的页面
assay ./my-app -e app.html        # 或者指定文件夹中的某个页面

assay ./my-app --report out.html  # 同时生成带截图的 HTML 报告
assay ./my-app --json             # 以 JSON 格式输出完整的运行结果
assay ./my-app --one-line         # 供脚本和智能体读取的简短摘要
assay ./my-app --surface          # 列出找到的控件后停止
```

assay 接受一个路径。路径是文件夹时，assay 托管这个文件夹并打开其中的 `index.html`。路径以 `.html`、`.htm` 或 `.xhtml` 结尾时，这个文件就是要检查的页面，assay 托管它所在的文件夹，因为页面会加载旁边的文件。

只要有任何检查（check）失败，退出码就不为零。除了首次运行时下载 Chromium 以外，assay 只在你要求时才向磁盘写入内容。

---

## <a id="options"></a>选项

| 选项 | 作用 |
|---|---|
| `-e ENTRY`, `--entry ENTRY` | 打开文件夹中的 `ENTRY`，而不是 `index.html` |
| `--report FILE` | 同时把 HTML 报告写入 `FILE`，其中包含每项检查前后的页面截图 |
| `--json` | 以 JSON 输出完整的运行结果，取代默认输出 |
| `--one-line` | 输出简短摘要，说明检查了什么、哪些被标记为有问题（flagged） |
| `--if-page` | 除非路径是 assay 能检查的页面，否则不输出任何内容并以 0 退出 |
| `--surface` | 输出页面提供的控件（control）后停止，不运行任何检查 |
| `--version` | 输出已安装的版本后退出 |
| `-h`, `--help` | 输出选项说明后退出 |

`--if-page` 供每次编辑后都会运行的钩子（hook）使用。大多数编辑改的并不是页面，加上这个选项后，assay 对这些情况保持安静，不会把错误输出到智能体（agent）的对话中。

同时给出 `--json` 和 `--one-line` 时，assay 输出 JSON。

---

## <a id="what-assay-prints"></a>assay 的输出

### <a id="the-default-output"></a>默认输出

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

第一行统计规划、执行、通过和失败的检查数。之后按运行顺序列出每项检查，包含它的编号、结果和它做了什么。

| 结果 | 含义 |
|---|---|
| `[ok]` | 检查已运行，没有发现问题 |
| `[FAILED]` | 违反了某条规则（rule），以 `→` 开头的那一行说明发生了什么 |
| `[not checked]` | 检查无法执行，这种情况从不算作失败 |

如果一项失败重复了前面的某个问题（finding），它会显示 `↳ same finding as C003`（与 C003 是同一个问题）而不是消息，第一行也会说明有多少项失败是重复的。

检查的编号为 `C001`、`C002`，依此类推。针对整次运行、任何单项检查都无法单独发现的问题，编号为 `F001`、`F002`。两个针对整个页面的问题编号为 `C000`。

---

### <a id="the-short-summary"></a>简短摘要

没有发现问题时，`--one-line` 输出一句话。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

发现问题时，它为每个问题输出一行，重复的问题会指明第一个问题，而不会重复它的消息。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

如果有检查无法执行，第一行会说明有多少项，这样页面不会因为从未运行的检查而被报告为没有问题。来自页面的文字会被压成一行可打印字符，所以页面无法往摘要里添加自己的行。

---

### <a id="json"></a>JSON

`--json` 输出一个对象，包含以下字段。

| 字段 | 内容 |
|---|---|
| `version` | assay 的版本 |
| `entry` | 打开的页面 |
| `planned`, `passed`, `failed` | 规划、通过和失败的检查数 |
| `works` | 没有检查失败时为 `true` |
| `sandboxed` | 页面在 Chromium 的沙箱中运行时为 `true` |
| `surface` | 找到的每个控件，包含它的 `kind`、`selector`、`label` 以及是否 `enabled` |
| `cases` | 每项检查，见下文 |
| `links` | 问题之间的每个关联，包含 `from`、`kind`、`to` 和 `why` |
| `console_errors` | 页面输出到控制台的错误 |
| `failed_requests` | 页面发出但失败了的请求 |

`cases` 中的每一项包含以下字段。

| 字段 | 内容 |
|---|---|
| `id` | 检查的编号，例如 `C003` |
| `what` | 用文字描述这项检查做了什么 |
| `outcome` | `passed`、`failed` 或 `unknown`，其中 `unknown` 表示未检查 |
| `detail` | 检查失败时，说明哪里出了问题 |
| `measured` | assay 测量到的内容，无论检查通过还是失败 |
| `acts` | 这项检查按顺序执行的操作 |
| `rules` | 这项检查违反的规则的名称 |
| `key` | 问题的名称，添加检查后也保持不变，格式为 `rule@what the check did` |
| `links` | 从这个问题到另一个问题的关联，包含 `kind`、`to` 和 `why` |

控制台错误和失败的请求从不会让检查失败，因为页面即使输出了错误或缺少一个图标，也可能正常工作。当确实有检查失败时，它们往往是最值得先看的内容。

---

### <a id="the-controls"></a>控件列表

`--surface` 列出 assay 在页面上找到的内容，每行一个控件，包含它的类型、选择器、标签和以像素为单位的尺寸。

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter --surface
kind: page
- button `#inc` 'Increment' 151x52
- button `#reset` 'Reset' 107x52
```

---

## <a id="exit-codes"></a>退出码

| 退出码 | 情况 |
|---|---|
| 0 | 没有检查失败 |
| 1 | 至少有一项检查失败 |
| 2 | 页面无法检查，原因是页面不存在、需要构建，或者无法安装 Chromium |

使用 `--if-page` 时，assay 以 0 而不是 2 退出。`--surface` 在列出控件后以 0 退出。

---

## <a id="the-html-report"></a>HTML 报告

`--report` 会生成一个可以直接打开的页面，展示每项检查前后的页面。

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="assay 报告中的一项检查，检查对象是一个标签筛选器。标签被点击两次后外观恢复原样，但列表仍处于筛选状态。图中列出了操作步骤、原因，以及检查前后的页面截图，列表从十二项变成了一项。">

对于每项检查，报告会展示它的操作、结果和原因，以及 assay 测量到的内容。报告是一个 HTML 文件，截图放在它旁边一个以报告命名的文件夹中，所以 `--report out.html` 还会写入 `out-shots/`。报告不从互联网加载任何内容，所以可以直接从磁盘或 CI 产物中打开，并且会跟随你的浅色或深色主题。

---

## <a id="colour"></a>颜色

在终端中，assay 会给结果着色，让失败更显眼。输出到管道或文件时没有颜色。设置 `NO_COLOR` 环境变量会关闭颜色，设置 `FORCE_COLOR` 会在任何地方开启颜色。

---

## <a id="errors"></a>错误

assay 把以下消息输出到错误流。

| 消息 | 含义 |
|---|---|
| `assay: my-app/index.html doesn't exist` | 路径中没有可以打开的页面 |
| `assay: index.html loads /src/main.jsx, which a browser can't run without a build step.` | 这个文件夹是源码目录。assay 会输出需要你自己运行的构建命令，它自己从不运行 |
| `assay: index.html loads /src/main.jsx, which a browser can't run, but dist/index.html is built.` | 这个文件夹中有一份构建好的副本，assay 会输出应该检查的路径 |
| `assay: there's no index.html here, but there's a package.json, so the page probably comes from a build step.` | 这个文件夹是一个尚未构建的项目 |
| `assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.` | 首次运行正在下载 Chromium |
| `assay: playwright isn't installed. Run pip install assay-ui to install it.` | 当前的 Python 中缺少 assay 自己的依赖 |
| `assay: Chromium's sandbox couldn't start on this system, so the page ran without it.` | 页面仍然完成了检查。以 root 身份运行或在某些容器中运行时，沙箱无法启动 |

当某一项检查无法执行时，运行会继续，这项检查会被报告为未检查（not checked）并附上原因，例如页面替换了 assay 依赖的某个内置函数。

---

## <a id="from-python"></a>在 Python 中使用

### <a id="checking-a-page"></a>检查页面

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

`check` 接受以下参数。

| 参数 | 作用 |
|---|---|
| `folder` | 存放页面的文件夹，或者页面本身，解读方式与命令解读路径的方式相同 |
| `entry` | 在文件夹中要打开的页面，默认是 `index.html` |
| `criteria` | 你自己编写的检查，在 assay 的检查之前运行，见下文 |
| `shots` | 用来存放每项检查前后截图的文件夹。不提供时，不会向磁盘写入任何内容 |

它返回一份报告，包含以下属性。

| 属性 | 内容 |
|---|---|
| `works` | 没有检查失败时为 `True` |
| `plan` | 按运行顺序排列的每项检查 |
| `results` | 每项检查的结果，以检查的编号为键 |
| `failing` | 失败的结果，你自己的标准排在前面 |
| `unchecked` | 无法执行的检查的结果 |
| `surface` | assay 找到的控件 |
| `console_errors`, `failed_requests` | 页面输出的错误和失败的请求 |
| `summary()`, `render()` | 输出的第一行，以及完整输出，均为文本 |

每个结果包含它运行的 `case`、值为 `"passed"`、`"failed"` 或 `"unknown"` 的 `outcome`、说明哪里出了问题的 `detail`、assay 测量到的 `evidence`、它违反的 `rules`，以及它的 `key`。

---

### <a id="acceptance-criteria"></a>验收标准

assay 不知道一个控件应该做什么，所以能运行但做错了事的页面通常都会通过检查。要检查页面应该做什么，请自己编写一项检查，并把它作为验收标准（acceptance criteria）传入。

```python
from assay import Case, check

total = Case(
    id="A001",
    what="adding 10 and 20 shows a total of 30",
    acts=[{"fill": "#price=10"}, {"click": "#add"},
          {"fill": "#price=20"}, {"click": "#add"}],
    expect={"want": "Total: 30"},
    origin="criterion",
)

report = check("./my-app", criteria=[total])
```

在总计算错的页面上，这条标准会失败，并给出下面的说明。

```
the page doesn't contain 'Total: 30'
```

`acts` 是要按顺序执行的操作。每个操作由一个动词和它的目标组成。

| 操作 | 作用 |
|---|---|
| `{"click": "#add"}` | 点击选择器匹配的元素。也可以使用控件上的文字，例如 `{"click": "Add"}` |
| `{"fill": "#price=10"}` | 把 `=` 后面的值输入到选择器匹配的输入框中 |
| `{"press": "Enter"}` | 按下一个键 |
| `{"reload": "page"}` | 重新加载页面 |
| `{"wait": "2"}` | 等待相应的秒数，最多 10 秒 |

`expect` 说明之后必须成立的条件。

| 预期 | 必须成立的条件 |
|---|---|
| `{"want": "Total: 30"}` | 页面上出现这段文字 |
| `{"unchanged": True}` | 页面保持原样 |
| `{"quiet": True}` | 没有特定要求，所以只有页面抛出错误时这项检查才会失败 |
| `{}` | 页面上有内容发生变化 |

assay 会自己给每项检查编号，所以标准的 `id` 在结果中会被替换。`--json` 会输出 assay 规划的每项检查的 `acts`，从中可以看到 assay 如何书写每种操作。

---

### <a id="listing-the-controls"></a>列出控件

`look` 会打开页面并列出其中的控件，但不运行任何检查，与 `--surface` 的做法相同。

```python
from assay import look

opened = look("./my-app")
print(opened.surface.render())
```

---

本文是 [usage.md](usage.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
