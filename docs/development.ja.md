<!-- i18n-source: docs/development.md 8f7e644727f16095e74e0ce33482485d38527a96 -->

<h1 align="center">開発</h1>

<p align="center"><a href="../README.ja.md">assay</a> › 開発</p>

<p align="center"><a href="development.md">English</a> · <a href="development.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="development.ko.md">한국어</a> · <a href="development.ru.md">Русский</a></p>

<p align="center">assay のコードの構成と、変更の種類ごとに必要なことを説明します。</p>

---

## <a id="contents"></a>目次

- [コードの構成](#how-the-code-is-laid-out)
- [ルールを変更する](#changing-a-rule)
- [テスト](#tests)
- [ベンチマーク](#benchmarks)
- [harness を追加する](#adding-a-harness)
- [ドキュメントを変更する](#changing-the-docs)
- [ドキュメント](#docs)

---

## <a id="how-the-code-is-laid-out"></a>コードの構成

**`src/assay/`** はツール本体です。

- `browser.py` は、フォルダーを配信し、ページを開き、読み込みを待ち、ピクセル、テキスト、入力欄、スタイルを読み取ります。測定するだけで、何かが失敗したかどうかは判断しません。
- `surface.py` は、描画されたページをコントロールの一覧に変換し、チェックの計画を組み立てます。
- `run.py` には、全体を実行する `check()` と、各チェックの前後のページを比較して成功かどうかを判断する `judge()` があります。ほとんどのルールはここにあります。
- `qa.py` は、計画を実行して結果を保持します。ブラウザーのコードを含まないので、ブラウザーなしでテストできます。
- `links.py` は、同じ指摘（finding）にあたる失敗をまとめます。完了した結果を読むだけで、結果を変えることはありません。
- `report.py` は、`--report` のページを書き出します。
- `tint.py` は、ターミナルの色を扱います。
- `cli.py` は、`assay` コマンドです。

**`plugins/assay/`** は skill とプラグインです。

- `skills/checking-a-page/` が skill で、1 つの Markdown ファイルです。
- `hooks/pages.py` は、ターンで変更されたページをファイルの更新時刻から見つけます。
- `hooks/check_pages.py` は、それらのページをチェックし、結果を必ず報告します。

**`benchmarks/`** は assay の評価に使うページです。

- `generated/` には、AI が書いたプログラムとその正解リスト（answer key）が入っています。
- `planted/` には、正常に動くプログラムと、意図的にバグを仕込んだ複製が入っています。
- `harness/` には、2 つの採点スクリプトと、指摘のまとめ方の正解リストが入っています。

**`tests/`** はテストスイートです。**`docs/`** には、ドキュメントと、実際の実行結果から README の画像を描くスクリプトが入っています。

---

## <a id="changing-a-rule"></a>ルールを変更する

ルールとは、チェックが失敗したかどうかを決めるものすべてです。ほとんどは `run.py` の `judge` にあり、ルールを働かせるチェックは `surface.py` で組み立てます。

1. **テストを 2 つ書きます。** 1 つはルールが問題ありと判定すべきページ、もう 1 つは判定してはならないページです。純粋な比較は、ブラウザーが不要な `tests/test_judge.py` に入れます。実際のページが必要なものは `tests/test_end_to_end.py` に入れます。
2. **両方のベンチマークを実行**し、変更前と変更後の数値をプルリクエストに書きます。テストでは正常に動くプログラムでの誤検知（false alarm）は見つけられませんが、ベンチマークなら見つけられます。
3. **誤検知は見逃し（miss）より高くつきます。** バグを 3 つ多く見つけても、正常に動くページを 1 つ問題ありと判定するルールは、改善ではありません。誤検知があると、正しかったコードを誰かが変更することになるからです。
4. **何が起きたかを平易な言葉で伝えます。** メッセージは、assay が何をして、ページがどう反応したかを伝えます。たとえば *when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late*（同じ状態から 2 回押すと、1 回目は何も変わらず、2 回目でページが変わったので、反応が 1 回分遅れている）のように書きます。*this page is broken*（このページは壊れている）のような結論だけを示すことはなく、ルールを読んでいない人にも意味が通じるようにします。
5. **ドキュメントに書きます。** `docs/how-it-works.md` の、そのルールを働かせる操作の項目にルールを追加し、assay が何をするか、どんなメッセージを出力するか、どんなときになぜ報告しないかを書きます。

誤検知の修正には、問題ありと判定されたページが必要です。そのページを、問題なしのままでなければならないテストとして追加します。

---

## <a id="tests"></a>テスト

```bash
pytest -q
```

テストスイート全体には約 25 分かかります。ほとんどのテストが実際のブラウザーを操作するからです。`tests/test_judge.py`、`tests/test_plan.py`、`tests/test_links.py`、`tests/test_perform.py`、`tests/test_translations.py` はブラウザーが不要で数秒で終わるので、作業中はこれらを実行してください。時間の大半は `tests/test_end_to_end.py` にかかり、ブラウザーがない場合は失敗ではなくスキップになります。

CI は、プルリクエストごとに Python 3.10、3.11、3.12、3.13、3.14 でテストスイート全体を実行し、さらに両方のベンチマークの採点スクリプトを短く実行します。すべてが通るまでマージされません。

バグの修正には、修正前に失敗し、修正後に通るテストが必要です。

---

## <a id="benchmarks"></a>ベンチマーク

```bash
python benchmarks/harness/generated.py    # 生成されたセット
python benchmarks/harness/planted.py      # バグを仕込んだセット
```

ルールまたは `benchmarks/` を変更するときは、変更前と変更後に両方の採点スクリプトを実行する必要があります。それぞれが要約を 1 行出力するので、両方の行をプルリクエストに書きます。変更が改善と見なされるのは、正常に動くページを問題ありと判定せずに、より多くのバグを見つけた場合だけです。

正解リストの判定は手で書かれています。変更によって assay がベンチマークのプログラムについて新しい内容を報告するようになった場合、その新しい指摘が何であるかを記録するまで、採点スクリプトは何も書き込みません。

[Harness](../benchmarks/harness/README.md)

---

## <a id="adding-a-harness"></a>harness を追加する

- **harness（エージェントの実行環境）が skill を読み込む場合は、** インストール手順を `docs/harnesses.md` に追加し、`plugins/assay/skills/checking-a-page/` を指すようにします。
- **独自のプラグイン形式がある場合は、** その marketplace ファイルをほかのファイル（`.claude-plugin/`、`.cursor-plugin/`、`.grok-plugin/`、`.agents/plugins/`、`.github/plugin/`）の隣に追加し、同じ場所に手順を書きます。
- **その harness で実際にテストし、** 使ったバージョンを書いてください。
- **数を更新します。** README、インストールのページ、harness のページ、プラグインの README はどれも、対応している harness の数を書いています。
- **報告するだけで、修正はしません。** skill とプラグインは、何を押して何が起きたかを伝えるだけで、それを理由にコードを編集しません。この方針を守ってください。

---

## <a id="changing-the-docs"></a>ドキュメントを変更する

ドキュメントは、簡体字中国語、日本語、韓国語、ロシア語でも提供しています。変更するのは英語だけにしてください。すると `tests/test_translations.py` が失敗しますが、これは想定どおりで、変更をマージする前にメンテナーが翻訳を更新します。

---

## <a id="docs"></a>ドキュメント

| ドキュメント | 内容 |
|---|---|
| [ドキュメントの翻訳](development/translating.md) | すべての翻訳が従う規約と、翻訳を最新に保つテストの仕組み |
| [用語集](development/glossary.md) | assay の用語に各言語で使う訳語 |

---

このページは [development.md](development.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
