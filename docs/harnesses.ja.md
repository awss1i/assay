<!-- i18n-source: docs/harnesses.md 35ce1703961c0b049eb853466b5b884081a86ff7 -->

<h1 align="center">harness に assay をインストールする</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="harnesses.ko.md">한국어</a> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">15 種類の harness（エージェントの実行環境）へのインストール手順です。そのうち 6 種類では、それぞれのプラグインコマンドで assay をインストールします。残りの 9 種類では skill のファイルを所定の場所にコピーします。この方法は、skill を読み込む harness ならどれでも使えます。</p>

---

## <a id="contents"></a>目次

- [提供されるもの](#what-you-get)
- [Claude Code](#claude-code)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [その他の harness、skill 単体での利用](#everywhere-else-the-skill-on-its-own)

---

## <a id="what-you-get"></a>提供されるもの

assay は次の 2 つで構成されています。

- **skill**。エージェントに対し、ページを書き終えたら `assay` を実行して結果を表示するよう指示します。
- **フック**。チェックを自動で実行します。

プラグインとしてインストールすると、両方が入ります。フックが動作するのは Claude Code と DeepSeek Harness で、ページに変更があったターンの終わりに毎回チェックが実行されます。それ以外の harness では、skill の指示に従ってエージェント自身がチェックを実行します。opencode と[その他の harness](#everywhere-else-the-skill-on-its-own) に挙げたものは skill だけをインストールし、DeepSeek Harness は Claude Code 用のブリッジを通じてフックだけを使います。

15 種類のどの harness でも、事前に `assay` が `PATH` 上にある必要があります。

```bash
pip install assay-ui           # Python 3.10 以上が必要
```

```bash
uv tool install assay-ui       # Python 3.10 以上がなくても uv がダウンロードします
```

```bash
pipx install assay-ui          # assay を専用の隔離環境にインストールします
```

---

## <a id="claude-code"></a>Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh は、同梱のブリッジを通じて Claude Code のフック設定を実行します。このブリッジはどのプロファイルにも含まれていないため、`$DSH_HOME/cordis.patch.yml` に追加してください。このファイルは各プロファイル自身のレイヤーの後に適用されるので、`web`、`headless`、そして自分で作ったプロファイルのすべてに効きます。

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: /abs/path/to/assay/plugins/assay/hooks/hooks.json
        pluginRoot: /abs/path/to/assay/plugins/assay
```

`$DSH_HOME` は、設定しない限り `~/.dsh` です。フックは独自の作業ディレクトリで実行されるため、どちらのパスも絶対パスで指定します。`dsh --dump-config` は合成後の設定ツリーを出力するので、ブリッジが組み込まれたかどうかはこれで確認できます。

1 つのプロファイルだけに適用したい場合は、同じブロックを代わりにそのプロファイルの `cordis.patch.yml` に書くか、実行ごとに `--patch` で渡してください。

---

## <a id="opencode"></a>opencode

```bash
mkdir -p .claude/skills
cp -r plugins/assay/skills/checking-a-page .claude/skills/
```

opencode は `.claude/skills/`、`.opencode/skills/`、`.agents/skills/`、`~/.config/opencode/skills/` を読み込みます。おすすめは `.claude/skills/` です。Claude Code もこのフォルダーを読み込むので、1 つのフォルダーで両方に対応できます。

---

## <a id="devin-cli"></a>Devin CLI

```bash
devin plugins install awss1i/assay#plugins/assay
```

プラグインは `plugins/assay` にあり、`#` はその場所を参照するよう Devin に伝えるための記法です。更新するには `devin plugins update assay` を実行します。

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

## <a id="everywhere-else-the-skill-on-its-own"></a>その他の harness、skill 単体での利用

*Antigravity、Codex App、Codex CLI、Cursor、Gemini CLI、Grok Build CLI、Kimi Code、Pi、Hermes Agent。*

assay はこれらの harness の形式に合わせたプラグインを提供していないため、skill をファイルとしてインストールします。skill は 1 つの Markdown ファイルで、skill や指示ファイルを読み込む環境ならどこでも動作します。

[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page) を、使っている harness が skill を読み込むフォルダーにコピーしてください。たとえば、Hermes Agent が読み込むプロジェクトの `.agents/skills/` などです。あるいは、このファイルの内容を `AGENTS.md` に貼り付けても構いません。

フックがない場合、チェックは毎ターンの終わりに実行されるのではなく、いつ実行するかをエージェントが判断します。

**[skill の仕組み →](../plugins/assay/README.ja.md#the-skill)**

---

このページは [harnesses.md](harnesses.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
