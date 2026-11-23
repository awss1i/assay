<!-- i18n-source: docs/install.md c51339dcc8b0355b209153fdf0186ea21a55095f -->

<h1 align="center">インストール</h1>

<p align="center"><a href="../README.ja.md">assay</a> › インストール</p>

<p align="center"><a href="install.md">English</a> · <a href="install.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="install.ko.md">한국어</a> · <a href="install.ru.md">Русский</a></p>

<p align="center">assay をインストールするすべての方法です。</p>

---

## <a id="contents"></a>目次

- [pip](#pip)
- [uv](#uv)
- [pipx](#pipx)
- [Chromium](#chromium)
- [アップデート](#updating)
- [アンインストール](#uninstalling)
- [コーディングエージェント](#coding-agents)

---

## <a id="pip"></a>pip

```bash
pip install assay-ui
```

assay には Python 3.10 以上が必要です。パッケージ名は `assay-ui` で、インストールされるコマンドは `assay` です。`pip` が見つからない場合は、`python3 -m pip install assay-ui` を使ってください。

---

## <a id="uv"></a>uv

```bash
uv tool install assay-ui
```

システムに 3.10 以上の Python がない場合、uv が assay 用の Python をダウンロードし、`assay` コマンドを `PATH` に追加します。

---

## <a id="pipx"></a>pipx

```bash
pipx install assay-ui
```

pipx は、ほかの Python パッケージとは別の専用の隔離環境に assay をインストールします。

---

## <a id="chromium"></a>Chromium

assay は Playwright を通じて Chromium でページを開きます。初回の実行時に Chromium がインストールされているかを確認し、なければダウンロードします。ダウンロードを始める前に、assay は次のメッセージを出力します。

```
assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.
```

pip でインストールした場合は、コンテナイメージのビルド時などに、あらかじめ Chromium をダウンロードしておけます。

```bash
python -m playwright install chromium
```

Linux では、Chromium にいくつかのシステムライブラリが必要です。ライブラリが足りずに初回の実行が失敗した場合は、次のコマンドで Chromium と一緒にインストールできます。

```bash
python -m playwright install --with-deps chromium
```

---

## <a id="updating"></a>アップデート

| インストール方法 | コマンド |
|---|---|
| pip | `pip install --upgrade assay-ui` |
| uv | `uv tool upgrade assay-ui` |
| pipx | `pipx upgrade assay-ui` |

`assay --version` で、インストールされているバージョンを表示します。

---

## <a id="uninstalling"></a>アンインストール

| インストール方法 | コマンド |
|---|---|
| pip | `pip uninstall assay-ui` |
| uv | `uv tool uninstall assay-ui` |
| pipx | `pipx uninstall assay-ui` |

assay をアンインストールしても、Chromium は Playwright のキャッシュに残ります。pip でインストールした場合は、assay をアンインストールする前に `python -m playwright uninstall` を実行すると、Playwright がダウンロードしたブラウザーを削除します。

---

## <a id="coding-agents"></a>コーディングエージェント

skill もプラグインも `assay` コマンドを実行するので、先に上記のいずれかのコマンドで assay をインストールしてください。そのあとの手順は harness（エージェントの実行環境）ごとに異なります。

| Harness | インストールされるもの |
|---|---|
| [Claude Code](harnesses.ja.md#claude-code) | skill とフック（プラグインとして） |
| [Codex](harnesses.ja.md#codex) | skill とフック（プラグインとして） |
| [Grok Build CLI](harnesses.ja.md#grok-build-cli) | skill とフック（プラグインとして） |
| [Cursor](harnesses.ja.md#cursor) | skill（プラグインとして） |
| [DeepSeek Harness](harnesses.ja.md#deepseek-harness) | skill はファイルのコピーで、フックは Claude Code ブリッジ経由で |
| [opencode](harnesses.ja.md#opencode) | skill（ファイルのコピーで） |
| [Devin CLI](harnesses.ja.md#devin-cli) | skill とフック（プラグインとして） |
| [Factory Droid](harnesses.ja.md#factory-droid) | skill とフック（プラグインとして） |
| [GitHub Copilot CLI](harnesses.ja.md#github-copilot-cli) | skill とフック（プラグインとして） |
| [Antigravity、Gemini CLI、Kimi Code、Pi、Hermes Agent](harnesses.ja.md#everywhere-else-the-skill-on-its-own) | skill（ファイルのコピーで） |

---

このページは [install.md](install.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
