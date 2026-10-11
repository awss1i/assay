<!-- i18n-source: README.md 8c074d8000142ff19d4c5491cdd2f2a8293ab8ad -->

<h1 align="center">assay</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

<p align="center">
  <a href="https://github.com/awss1i/assay/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-7c3aed" alt="python"></a>
  <a href="https://github.com/awss1i/assay/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-MIT-7c3aed" alt="licence"></a>
  <a href="https://github.com/sickn33/agentic-awesome-skills"><img src="https://img.shields.io/badge/listed%20in-agentic--awesome--skills-db2777" alt="listed in agentic-awesome-skills"></a>
  <a href="https://github.com/TheJambo/awesome-testing"><img src="https://img.shields.io/badge/listed%20in-awesome--testing-db2777" alt="listed in awesome-testing"></a>
</p>

<p align="center">
  <a href="#install">インストール</a> · <a href="#use">使い方</a> · <a href="#benchmarks">ベンチマーク</a> · <a href="#how-it-works">仕組み</a> · <a href="#why">なぜ assay なのか</a> · <a href="#limits">制限事項</a> · <a href="#contributing">コントリビューション</a> · <a href="#licence">ライセンス</a>
</p>

---

<p align="center"><strong>エージェントネイティブな Web ページ向け QA CLI。決定論的、テスト不要、LLM 不要。</strong></p>

<p align="center"><code>pip install assay-ui</code></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/run.svg" alt="ドラッグで並べ替えるリストに対して assay を実行しているターミナルです。ページから 7 件のチェックが計画され、1 件が成功、6 件が失敗しています。最初の失敗はページ上のどこもまったく変化しなかったことを示し、残りの 5 件は同じ指摘であることを示しています。">
</p>

<p align="center"><i>バグを含む、ドラッグで並べ替えるリストをチェックした例。</i></p>

---

assay はページを Chromium で開き、ページ上のコントロールをすべて見つけ出して、そのすべてを実際に操作し、うまくいかなかった点を報告します。

- **テストを書く必要はありません。** assay は、ページ上で見つけたコントロールをもとにチェックを組み立てます。
- **LLM は使いません。** API キーも費用も不要で、何度実行しても同じ結果になります。
- **コーディングエージェントと連携します。** 15 種類の harness（エージェントの実行環境）に対応した skill を使うと、エージェントは自分が書いたページを 1 つずつチェックします。Claude Code と DeepSeek Harness 向けのプラグインを使えば、ターンが終わるたびにチェックが自動で実行されます。
- **重複をまとめます。** 1 つのバグが複数のチェックを失敗させた場合、2 件目以降は同じメッセージを繰り返さず、*same finding as C003*（C003 と同じ指摘）と表示します。

---

## <a id="install"></a>インストール

```bash
pip install assay-ui           # Python 3.10 以上が必要
```

```bash
uv tool install assay-ui       # Python 3.10 以上がなくても uv がダウンロードします
```

```bash
pipx install assay-ui          # assay を専用の隔離環境にインストールします
```

`pip` が見つからない場合は、`python3 -m pip install assay-ui` を使ってください。初回の実行時には、必要に応じて Chromium がダウンロードされます。

assay 自体の開発に参加する場合は、次のようにします。

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
```

### <a id="for-coding-agents"></a>コーディングエージェント向け

まず上記の CLI をインストールしてから、**[harness のセットアップ →](https://github.com/awss1i/assay/blob/main/docs/harnesses.ja.md)** の手順に従い、対応している 15 種類の harness のいずれかに skill またはプラグインを追加してください。

---

## <a id="use"></a>使い方

```console
assay ./my-app                    # このフォルダーの index.html をチェック
assay ./my-app --report out.html  # スクリーンショット付きの HTML レポートも書き出す
assay ./my-app --one-line         # スクリプトやエージェント向けの短い要約
```

失敗が 1 つでもあれば終了コードは 0 以外になります。また、指定しない限りディスクには何も書き込みません。

**[すべてのフラグ、実行例、Python API、HTML レポート →](https://github.com/awss1i/assay/blob/main/docs/usage.ja.md)**

### <a id="with-coding-agents"></a>コーディングエージェントで使う

**skill** は、対応している 15 種類の harness すべてで動作します。対象は Claude Code、DeepSeek Harness、opencode、Antigravity、Codex App、Codex CLI、Cursor、Devin CLI、Factory Droid、Gemini CLI、GitHub Copilot CLI、Grok Build CLI、Kimi Code、Pi、Hermes Agent です。skill はエージェントに対し、ページを書き終えたら assay を実行し、返答の最後に次のような結果を載せるよう指示します。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**プラグイン**（Claude Code と DeepSeek Harness 向け）はフックを追加し、ページに変更があったターンの終わりに毎回チェックを自動で実行します。どちらの方法でも、エージェントは assay が見つけた内容を報告するだけで、あなたが頼まない限り、それを理由にコードを変更することはありません。

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

**[skill とプラグインの仕組み →](https://github.com/awss1i/assay/blob/main/plugins/assay/README.ja.md)**

---

## <a id="benchmarks"></a>ベンチマーク

assay はこのリポジトリにある 2 組のページで評価しています。以下の数値はすべて採点スクリプトが書き込んだものです。

**AI が書いたページ。** 75 個のプロンプトから AI がそれぞれ 3 回ずつ書いた、225 個の小さな Web アプリです。その後、人が実際に開いて試しました。

assay は壊れている 20 ページのうち 15 ページで本物のバグを見つけ、正常に動く 205 ページのうち問題ありと判定したのは 0 ページでした。[すべてのページと結果](https://github.com/awss1i/assay/blob/main/bench/README.md)。

**意図的にバグを仕込んだページ。** assay の存在を知らされていない別のエージェントが、正常に動く 10 個のアプリそれぞれの複製に、自分で選んだバグを 5 個ずつ仕込み、その一覧を書き出しました。

assay は仕込んだ 50 個のバグのうち 12 個を見つけ、元の 10 ページのうち問題ありと判定したのは 0 ページでした。[すべてのバグと結果](https://github.com/awss1i/assay/blob/main/bench/planted/README.md)。

---

## <a id="how-it-works"></a>仕組み

assay は次の 5 つの手順で動きます。

1. フォルダーを localhost で配信し、ページを Chromium で開きます。
2. ページ上のコントロールが変化しなくなるまで待ちます。
3. ブラウザーが描画するコントロールをすべて列挙します。クリックできる div、ドラッグハンドル、編集可能な領域も含みます。
4. それらのコントロールからチェックを計画します。たとえば、すべてのボタンを 1 回押す、2 回押す、入力欄に空の文字列、普通の文字列、非常に長い文字列、HTML を含む文字列を入力する、すべてのドロップダウンを変更する、キャンバスに描画する、フォームに入力して送信する、などです。
5. 各チェックを新しいタブで実行し、実行前後のページを比較します。

assay はページが何のためのものかを知りません。そのため、押しても何も変わらないボタンがあるだけでは失敗とみなしません。代わりに、ページが自己矛盾している（the page contradicts itself）箇所を報告します。たとえば次のような場合です。

- ページがエラーを投げる
- 「Undo」が 1 回目には何もせず、2 回目で動く
- リストが空なのに、項目数の表示が 1 になっている
- 項目を追加すると合計が増えるのに、削除しても減らない
- 数値があるべき場所に `NaN` が表示される
- どのコントロールを操作しても、ページがまったく反応しない

**[すべてのルール →](https://github.com/awss1i/assay/blob/main/docs/how-it-works.ja.md)**

---

## <a id="why"></a>なぜ assay なのか

Playwright や Cypress には、誰かが書いたテストが必要です。ビジュアルリグレッションテストには、基準となるスクリーンショットが必要です。モデルにコードをレビューさせる方法では、コードを読むだけで実行はしません。assay は事前に何も準備せずに、コードを実際に実行します。

|  | テストを書く必要 | ベースラインの必要 | プログラムの実行 |
|---|---|---|---|
| Playwright / Cypress | あり | なし | する、書いた部分だけ |
| Percy / Chromatic | なし | **あり** | スクリーンショットを撮る |
| モデルにレビューさせる | なし | なし | **しない、ソースを読むだけ** |
| **assay** | **なし** | **なし** | **する、すべて** |

---

## <a id="limits"></a>制限事項

- **意図はチェックできません。** 動きはするものの間違った処理をするページ（たとえば合計の計算を間違えるページ）は、たいていチェックを通過します。そうした点を確かめるには、Python から受け入れ基準（acceptance criteria）を渡してください。
- **対象は Web ページのみです。** ローカルフォルダーから配信したページを 1 つずつチェックします。クロール、ログイン、実際のネットワーク通信は行いません。
- **対象はビルド済みの出力のみです。** `npm install` やビルドは実行しません。ソースツリーを指定すると、先に何を実行すべきかを教えてくれます。
- **終了したゲームは壊れているように見えることがあります。** 再開する手段がないまま終了したゲームは反応しなくなるため、何も反応しないページとして報告されることがあります。
- **速度。** ほとんどのページは数秒から 1 分で終わります。ベンチマークのページには、各ページの所要時間と、計測に使ったマシンが載っています。

---

## <a id="contributing"></a>コントリビューション

バグや誤検知（false alarm）は Issue で報告し、変更はプルリクエストで送ってください。質問やアイデアの共有は [Discussions](https://github.com/awss1i/assay/discussions) でどうぞ。詳しくは **[CONTRIBUTING.md](https://github.com/awss1i/assay/blob/main/CONTRIBUTING.md)** を参照してください。

---

## <a id="licence"></a>ライセンス

MIT ライセンスです。

---

このページは [README.md](README.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
