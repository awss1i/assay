<!-- i18n-source: README.md 8c074d8000142ff19d4c5491cdd2f2a8293ab8ad -->

<h1 align="center">assay</h1>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

<p align="center">
  <a href="https://github.com/awss1i/assay/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-7c3aed" alt="python"></a>
  <a href="https://github.com/awss1i/assay/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-MIT-7c3aed" alt="licence"></a>
  <a href="https://github.com/sickn33/agentic-awesome-skills"><img src="https://img.shields.io/badge/listed%20in-agentic--awesome--skills-db2777" alt="listed in agentic-awesome-skills"></a>
  <a href="https://github.com/TheJambo/awesome-testing"><img src="https://img.shields.io/badge/listed%20in-awesome--testing-db2777" alt="listed in awesome-testing"></a>
</p>

<p align="center">
  <a href="#install">安装</a> · <a href="#use">使用</a> · <a href="#benchmarks">基准测试</a> · <a href="#how-it-works">工作原理</a> · <a href="#why">为什么选择 assay</a> · <a href="#limits">局限</a> · <a href="#contributing">参与贡献</a> · <a href="#licence">许可证</a>
</p>

---

<p align="center"><strong>智能体原生的网页 QA CLI。结果确定、无需编写测试、不依赖 LLM。</strong></p>

<p align="center"><code>pip install assay-ui</code></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/run.svg" alt="终端里，assay 正在检查一个靠拖动来排序的列表。assay 根据页面规划了 7 项检查，1 项通过，6 项失败。第一项失败指出页面上没有任何变化，其余五项指出它们与第一项是同一个问题。">
</p>

<p align="center"><i>检查一个带 bug 的拖动排序列表。</i></p>

---

assay 会在 Chromium 中打开你的页面，找出页面上的每个控件（control），逐一操作，然后报告哪里出了问题。

- **无需编写测试。** assay 根据在页面上找到的控件生成检查（check）。
- **不依赖 LLM。** 不需要 API 密钥，不产生费用，每次运行的结果都相同。
- **支持编程智能体（coding agent）。** 一个可在 15 种 harness（智能体运行框架）中使用的 skill 会让智能体检查它写出的每个页面，另有一个适用于 Claude Code 和 DeepSeek Harness 的插件（plugin），会在每一轮（turn）结束后自动运行检查。
- **合并重复的问题（finding）。** 当一个 bug 导致多项检查失败时，后面的检查会显示 *same finding as C003*（与 C003 是同一个问题），而不会重复同一条消息。

---

## <a id="install"></a>安装

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # 没有 Python 3.10+ 时由 uv 下载一个
```

```bash
pipx install assay-ui          # 把 assay 安装在单独的隔离环境中
```

如果找不到 `pip`，请改用 `python3 -m pip install assay-ui`。首次运行时，assay 会在需要时下载 Chromium。

如果要参与 assay 本身的开发，请运行以下命令。

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
```

### <a id="for-coding-agents"></a>用于编程智能体

先按上文安装 CLI，再按照 **[harness 安装指南 →](https://github.com/awss1i/assay/blob/main/docs/harnesses.zh-CN.md)**，在已支持的 15 种 harness 中的任意一种里添加 skill 或插件。

---

## <a id="use"></a>使用

```console
assay ./my-app                    # 检查该文件夹中的 index.html
assay ./my-app --report out.html  # 同时生成带截图的 HTML 报告
assay ./my-app --one-line         # 供脚本和智能体读取的简短摘要
```

只要有任何检查失败，退出码就不为零。除非你要求，assay 不会向磁盘写入任何内容。

**[全部参数、完整示例、Python API 和 HTML 报告 →](https://github.com/awss1i/assay/blob/main/docs/usage.zh-CN.md)**

### <a id="with-coding-agents"></a>配合编程智能体使用

**skill** 可在全部 15 种受支持的 harness 中使用：Claude Code、DeepSeek Harness、opencode、Antigravity、Codex App、Codex CLI、Cursor、Devin CLI、Factory Droid、Gemini CLI、GitHub Copilot CLI、Grok Build CLI、Kimi Code、Pi 和 Hermes Agent。它让你的智能体在写完页面后运行 assay，并在回复末尾附上结果，如下所示。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**插件**（适用于 Claude Code 和 DeepSeek Harness）会添加一个钩子（hook），在每一轮修改了页面的对话结束时自动运行检查。无论使用哪种方式，智能体都会报告 assay 发现的问题，除非你要求，否则不会因此修改代码。

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

**[skill 和插件的工作方式 →](https://github.com/awss1i/assay/blob/main/plugins/assay/README.zh-CN.md)**

---

## <a id="benchmarks"></a>基准测试

assay 的评分基于本仓库中的两组页面，下面的每个数字都由评分脚本写入。

**AI 编写的页面。** AI 根据 75 个提示词各写了三次，得到 225 个小型网页应用，再由人逐一打开试用。

assay 在 20 个有问题的页面中找到了其中 15 个页面的真实 bug，205 个正常页面中有 0 个被标记为有问题。[每个页面及其结果](https://github.com/awss1i/assay/blob/main/bench/README.md)。

**人为植入 bug 的页面。** 另一个从未被告知 assay 存在的智能体拿来 10 个正常运行的应用，在每个应用的副本中植入了 5 个由它自己挑选的 bug，然后把这些 bug 逐一列出。

assay 在植入的 50 个 bug 中找到了 12 个，10 个原始页面中有 0 个被标记为有问题。[每个 bug 及其结果](https://github.com/awss1i/assay/blob/main/bench/planted/README.md)。

---

## <a id="how-it-works"></a>工作原理

assay 分五步运行：

1. 在 localhost 上托管该文件夹，并用 Chromium 打开页面。
2. 等待页面上的控件不再变化。
3. 列出浏览器渲染出的所有控件，包括可点击的 div、拖动手柄和可编辑区域。
4. 根据这些控件规划检查：每个按钮按一次、再连按两次，在输入框中输入空文本、普通文本、超长文本和含 HTML 的文本，切换每个下拉框，在画布上绘制，填写并提交表单，等等。
5. 在全新的标签页中运行每项检查，并对比检查前后的页面。

assay 不知道你的页面是做什么用的，所以按钮按下后没有任何变化，本身并不算失败。assay 报告的是页面自相矛盾（the page contradicts itself）的地方，例如：

- 页面抛出错误，
- Undo 第一次按下没有反应，第二次才生效，
- 列表为空时，条目计数显示为 1，
- 添加条目时总计会增加，删除条目时却不减少，
- 本应显示数字的地方出现了 `NaN`，
- 操作任何控件，页面都没有任何反应。

**[全部规则 →](https://github.com/awss1i/assay/blob/main/docs/how-it-works.zh-CN.md)**

---

## <a id="why"></a>为什么选择 assay

Playwright 和 Cypress 需要有人事先写好测试。视觉回归测试需要一张参考截图。让模型审查代码，只是在阅读代码，并没有运行它。assay 会直接运行代码，无需事先准备任何东西。

|  | 需要编写测试 | 需要基线 | 运行程序 |
|---|---|---|---|
| Playwright / Cypress | 是 | 否 | 是，只运行你写到的部分 |
| Percy / Chromatic | 否 | **是** | 对程序截图 |
| 让模型审查 | 否 | 否 | **否，只阅读源码** |
| **assay** | **否** | **否** | **是，全部运行** |

---

## <a id="limits"></a>局限

- **无法检查意图。** 如果页面能运行但做错了事，比如总计算错了，通常会通过检查。要检查这类问题，请在 Python 中传入验收标准（acceptance criteria）。
- **仅限网页。** assay 每次检查一个页面，页面由本地文件夹提供。它不会爬取网站、不会登录，也不会发起真实的网络请求。
- **仅限构建产物。** assay 不会运行 `npm install`，也不会执行你的构建。如果你把它指向源码目录，它会告诉你需要先运行什么。
- **已结束的游戏可能看起来像坏了。** 游戏结束后如果无法重新开始，就不再响应操作，这可能被报告为页面毫无响应。
- **速度。** 大多数页面需要几秒到一分钟。基准测试（benchmark）页面列出了每个页面的耗时，以及测量时使用的机器。

---

## <a id="contributing"></a>参与贡献

发现 bug 或误报（false alarm），请提交 issue。修改请通过 pull request 提交。提问或分享想法，请前往 [Discussions](https://github.com/awss1i/assay/discussions)。详见 **[CONTRIBUTING.md](https://github.com/awss1i/assay/blob/main/CONTRIBUTING.md)**。

---

## <a id="licence"></a>许可证

MIT。

---

本文是 [README.md](README.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
