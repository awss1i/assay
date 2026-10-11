<!-- i18n-source: docs/usage.md 9be11eb39f461b4b49c164c323369eef0bdba264 -->

<h1 align="center">使用 assay</h1>

<p align="center"><a href="usage.md">English</a> · <b>简体中文</b> · <a href="usage.ja.md">日本語</a> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>

---

<p align="center">assay 在命令行和 Python 中的全部用法。</p>

---

## <a id="contents"></a>目录

- [命令](#the-command)
- [示例](#an-example)
- [HTML 报告](#the-html-report)
- [在 Python 中使用](#from-python)

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

除非你要求，assay 不会向磁盘写入任何内容。只要有任何检查（check）失败，退出码就不为零。

---

## <a id="an-example"></a>示例

assay 自带用于评分的基准测试（benchmark）页面，所以你现在就可以拿其中一个来运行。这里用的是一个小型绘图程序，它的 Undo 总是晚一次才有反应。

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

C016 就是失败的那项检查。第一次 Undo 什么也没做，第二次才完成撤销，所以 Undo 落后了一次。

---

## <a id="the-html-report"></a>HTML 报告

`--report` 会生成一个可以直接打开的页面，展示每项检查前后的页面。

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="assay 报告中的一项检查，检查对象是一个标签筛选器。标签被点击两次后外观恢复原样，但列表仍处于筛选状态。图中列出了操作步骤、原因，以及检查前后的页面截图，列表从十二项变成了一项。">

---

## <a id="from-python"></a>在 Python 中使用

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

---

本文是 [usage.md](usage.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
