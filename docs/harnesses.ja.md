<!-- i18n-source: docs/harnesses.md 754a27f7ad6e3db62fad6db5ec61f13ed63618f1 -->

<h1 align="center">harness に assay をインストールする</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="harnesses.ko.md">한국어</a> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">15 種類の harness（エージェントの実行環境）へのインストール手順です。そのうち 8 種類では、それぞれのプラグインコマンドで assay をインストールします。残りの 7 種類では skill のファイルを所定の場所にコピーします。この方法は、skill を読み込む harness ならどれでも使えます。</p>

---

## <a id="contents"></a>目次

- [提供されるもの](#what-you-get)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Grok Build CLI](#grok-build-cli)
- [Cursor](#cursor)
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

プラグインとしてインストールすると両方が入りますが、Cursor では skill だけが入ります。Claude Code、Codex、Grok Build CLI、Devin CLI、Factory Droid、GitHub Copilot CLI、DeepSeek Harness では、ページに変更があったターンの終わりに毎回フックがチェックを実行します。DeepSeek Harness では、skill はファイルをコピーして入れ、フックは Claude Code 用のブリッジを通じて使います。opencode と[その他の harness](#everywhere-else-the-skill-on-its-own) に挙げたものには skill だけが入り、skill の指示に従ってエージェント自身がチェックを実行します。

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

## <a id="codex"></a>Codex

Codex CLI では、マーケットプレイスを追加してからプラグインをインストールします。

```bash
codex plugin marketplace add awss1i/assay
codex plugin add assay@assay
```

次に新しいセッションを開始し、`/hooks` を開いて assay のフックを信頼済みにします。Codex は、あなたが信頼するまでプラグインのフックを実行しません。そのため、この手順を省くと skill だけが使える状態になります。更新するには `codex plugin marketplace upgrade assay` を実行します。

Codex App（ChatGPT のデスクトップアプリに組み込まれた Codex）では、上の `codex plugin marketplace add` コマンドを実行してからアプリを再起動し、「Plugins」にある assay マーケットプレイスから assay をインストールします。

---

## <a id="grok-build-cli"></a>Grok Build CLI

```bash
grok plugin marketplace add awss1i/assay
grok plugin install assay --trust
```

`--trust` を付けないと、Grok はフックを含むプラグインをインストールしません。インストールを止めて、`--trust` を付けてコマンドを再実行するよう求めます。インストールが成功すると、`grok inspect` の一覧に `checking-a-page` skill とフックが表示されます。更新するには、`grok plugin marketplace update` を実行してから `grok plugin update assay` を実行します。

---

## <a id="cursor"></a>Cursor

Cursor 2.5 以降のエディターでは、Agent のチャットに次のように入力します。

```
/add-plugin assay@https://github.com/awss1i/assay
```

Cursor CLI では、マーケットプレイスを追加してから、セッション内の `/plugin` で assay をインストールします。

```bash
agent plugin marketplace add https://github.com/awss1i/assay
```

どちらの方法でも skill が入ります。Cursor のフックは形式が異なるため、Cursor ではプラグインがフックを追加しません。プラグインを使わずに skill だけをインストールするには、skills CLI を使います。

```bash
npx skills add awss1i/assay --agent cursor       # このプロジェクト用、.agents/skills/ にインストール
npx skills add awss1i/assay --agent cursor -g    # すべてのプロジェクト用、~/.agents/skills/ にインストール
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh は、プロジェクト内の `.agents/skills/` と、すべてのプロジェクトで使う `~/.agents/skills/` から skill を読み込みます。`.claude/skills/` からは読み込みません。どちらかのフォルダーに skill をコピーしてください。

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

dsh のデフォルトの権限モードでは、プロジェクトの外に書き込むコマンドが止められます。最初のチェックでは Chromium をホームフォルダーにダウンロードするため、dsh がその許可を一度だけ求めることがあります。この確認を避けるには、最初のチェックを自分のシェルから実行してください。

フックについては、dsh は同梱のブリッジを通じて Claude Code のフック設定を実行します。このブリッジはどのプロファイルにも含まれていないため、`$DSH_HOME/cordis.patch.yml` に追加してください。このファイルは各プロファイル自身のレイヤーの後に適用されるので、`web`、`headless`、そして自分で作ったプロファイルのすべてに効きます。

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
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

opencode は `.agents/skills/`、`.opencode/skills/`、`.claude/skills/`、`~/.config/opencode/skills/` を読み込みます。おすすめは `.agents/skills/` です。DeepSeek Harness、Cursor、Hermes Agent もこのフォルダーを読み込むので、1 つのフォルダーで 4 つすべてに対応できます。

---

## <a id="devin-cli"></a>Devin CLI

Devin でプラグインを管理するにはサインインが必要なので、先に `devin auth login` を実行してください。

```bash
devin plugins install awss1i/assay#plugins/assay
```

プラグインは `plugins/assay` にあり、`#` はその場所を参照するよう Devin に伝えるための記法です。Devin Cloud のマニフェストではなく、このマシンだけにインストールするには `--local` を付けます。更新するには `devin plugins update assay` を実行します。Devin はプラグインのフックをベストエフォートで実行し、フックが失敗してもターンは止まりません。

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

対話形式で使う Droid では、あなたが信頼済みにしたフォルダーでしかフックが実行されません。

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

Copilot は、フックの報告内容をエージェントに渡さず、あなたに直接表示します。報告内容はターミナルの、エージェント向けの行の下に表示され、エージェントがそれを繰り返すことはありません。

---

## <a id="everywhere-else-the-skill-on-its-own"></a>その他の harness、skill 単体での利用

*Antigravity、Gemini CLI、Kimi Code、Pi、Hermes Agent。*

assay はこれらの harness の形式に合わせたプラグインを提供していないため、skill をファイルとしてインストールします。skill は 1 つの Markdown ファイルで、skill や指示ファイルを読み込む環境ならどこでも動作します。

[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page) を、使っている harness が skill を読み込むフォルダーにコピーしてください。たとえば、Hermes Agent が読み込むプロジェクトの `.agents/skills/` などです。あるいは、このファイルの内容を `AGENTS.md` に貼り付けても構いません。

フックがない場合、チェックは毎ターンの終わりに実行されるのではなく、いつ実行するかをエージェントが判断します。

**[skill の仕組み →](../plugins/assay/README.ja.md#the-skill)**

---

このページは [harnesses.md](harnesses.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
