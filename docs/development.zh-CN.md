<!-- i18n-source: docs/development.md 8f7e644727f16095e74e0ce33482485d38527a96 -->

<h1 align="center">开发</h1>

<p align="center"><a href="../README.zh-CN.md">assay</a> › 开发</p>

<p align="center"><a href="development.md">English</a> · <b>简体中文</b> · <a href="development.ja.md">日本語</a> · <a href="development.ko.md">한국어</a> · <a href="development.ru.md">Русский</a></p>

<p align="center">assay 的代码如何组织，以及每类修改需要什么。</p>

---

## <a id="contents"></a>目录

- [代码的组织方式](#how-the-code-is-laid-out)
- [修改规则](#changing-a-rule)
- [测试](#tests)
- [基准测试](#benchmarks)
- [添加 harness](#adding-a-harness)
- [修改文档](#changing-the-docs)
- [文档](#docs)

---

## <a id="how-the-code-is-laid-out"></a>代码的组织方式

**`src/assay/`**，工具本身：

- `browser.py` 负责托管文件夹、打开页面、等待页面加载，并读取像素、文字、输入框和样式。它只做测量，从不判断某项是否失败。
- `surface.py` 把渲染出的页面转换成控件（control）列表，并生成检查（check）计划。
- `run.py` 包含运行整个流程的 `check()`，以及 `judge()`。`judge()` 对比每项检查前后的页面，并判断检查是否通过。大多数规则（rule）都在这里。
- `qa.py` 运行计划并保存结果。它不含浏览器代码，所以不需要浏览器就能测试。
- `links.py` 把属于同一个问题（finding）的失败合并在一起。它只读取已完成的结果，从不更改结果。
- `report.py` 生成 `--report` 页面。
- `tint.py` 处理终端颜色。
- `cli.py` 是 `assay` 命令。

**`plugins/assay/`**，skill 和插件（plugin）：

- `skills/checking-a-page/` 是 skill，只有一个 markdown 文件。
- `hooks/pages.py` 根据文件时间找出一轮（turn）对话修改过的页面。
- `hooks/check_pages.py` 检查这些页面，并且一定会报告结果。

**`benchmarks/`**，用于给 assay 评分的页面：

- `generated/` 存放 AI 编写的程序及其标准答案（answer key）。
- `planted/` 存放正常工作的程序，以及人为植入 bug 的副本。
- `harness/` 存放两个评分脚本，以及用于核对问题合并的标准答案。

**`tests/`** 是测试套件。**`docs/`** 存放文档，以及根据真实运行结果绘制 README 中图片的脚本。

---

## <a id="changing-a-rule"></a>修改规则

规则是任何决定一项检查是否失败的东西。大多数规则位于 `run.py` 的 `judge` 中，而触发这些规则的检查在 `surface.py` 中生成。

1. **编写两个测试。** 一个是这条规则应该标记的页面，另一个是它绝不能标记的页面。纯粹的比较放在 `tests/test_judge.py` 中，它不需要浏览器。需要真实页面的测试放在 `tests/test_end_to_end.py` 中。
2. **运行两个基准测试（benchmark）**，并把修改前后的数字写进 pull request。测试发现不了正常程序上的误报（false alarm），而基准测试可以。
3. **误报的代价高于漏报（miss）。** 一条规则即使多找出三个 bug，只要把一个正常工作的页面标记为有问题，就不算改进，因为误报会让人去修改本来正确的代码。
4. **用平实的语言说明发生了什么。** 消息要说明 assay 做了什么、页面作何反应，例如 *when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late*（从同一个起点按两次，第一次按下时什么都没变，第二次才改变了页面，所以它的反应晚了一次）。消息从不只给出 *this page is broken*（这个页面坏了）这样的结论，而且应该让没读过这条规则的人也能看懂。
5. **写入文档。** 把这条规则添加到 `docs/how-it-works.md` 中触发它的操作之下，说明 assay 做了什么、输出什么消息，以及它在什么情况下不报告、为什么。

修复误报时，需要把被标记的那个页面添加为测试，并且这个测试必须保持没有问题。

---

## <a id="tests"></a>测试

```bash
pytest -q
```

完整的测试套件大约需要 25 分钟，因为大多数测试要驱动真实的浏览器。`tests/test_judge.py`、`tests/test_plan.py`、`tests/test_links.py`、`tests/test_perform.py` 和 `tests/test_translations.py` 不需要浏览器，几秒钟就能跑完，所以开发过程中先运行这些。`tests/test_end_to_end.py` 占用了大部分时间，没有浏览器时它会跳过而不是失败。

CI 会针对每个 pull request 在 Python 3.10、3.11、3.12、3.13 和 3.14 上运行完整的测试套件，并对两个基准测试评分脚本各做一次简短运行。全部通过后才能合并。

修复 bug 时，需要一个在修复前失败、修复后通过的测试。

---

## <a id="benchmarks"></a>基准测试

```bash
python benchmarks/harness/generated.py    # 生成的页面组
python benchmarks/harness/planted.py      # 植入 bug 的页面组
```

修改规则或 `benchmarks/` 时，需要在修改前后各运行两个评分脚本。每个脚本会输出一行摘要，两行都要写进 pull request。只有在找出更多 bug 且没有把正常工作的页面标记为有问题时，修改才算改进。

标准答案中的判断都是人工编写的。如果你的修改让 assay 在某个基准测试程序上报告了新的内容，在你记录下这个新问题是什么之前，评分脚本不会写入任何内容。

[Harness](../benchmarks/harness/README.md)

---

## <a id="adding-a-harness"></a>添加 harness

- **如果 harness（智能体运行框架）能读取 skill，** 把它的安装步骤添加到 `docs/harnesses.md`，并指向 `plugins/assay/skills/checking-a-page/`。
- **如果它有自己的插件格式，** 把它的 marketplace 文件放在其他同类文件旁边（`.claude-plugin/`、`.cursor-plugin/`、`.grok-plugin/`、`.agents/plugins/`、`.github/plugin/`），并在同一处写明用法。
- **在这种 harness 中实际测试，** 并说明你使用的版本。
- **更新数量。** README、安装页面、harness 页面和插件的 README 都写了支持多少种 harness。
- **只报告，从不修复。** skill 和插件只转述按下了什么、发生了什么，不会因此修改代码。请保持这一点。

---

## <a id="changing-the-docs"></a>修改文档

文档同时提供简体中文、日语、韩语和俄语版本。只需修改英文。之后 `tests/test_translations.py` 会失败，这是预期的，维护者会在合并之前更新译文。

---

## <a id="docs"></a>文档

| 文档 | 内容 |
|---|---|
| [翻译文档](development/translating.md) | 每份译文遵循的约定，以及测试如何确保译文保持最新 |
| [术语表](development/glossary.md) | 每种语言对 assay 术语的用词 |

---

本文是 [development.md](development.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
