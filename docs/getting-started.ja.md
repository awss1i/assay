<!-- i18n-source: docs/getting-started.md 87f5daae1ec1d0ee044476575debceac6d4328a6 -->

<h1 align="center">はじめに</h1>

<p align="center"><a href="../README.ja.md">assay</a> › はじめに</p>

<p align="center"><a href="getting-started.md">English</a> · <a href="getting-started.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="getting-started.ko.md">한국어</a> · <a href="getting-started.ru.md">Русский</a></p>

<p align="center">assay のインストールから日々の利用までを説明します。</p>

---

## <a id="contents"></a>目次

- [始める前に](#before-you-start)
- [ページをチェックする](#checking-a-page)
- [結果の読み方](#reading-the-result)
- [バグのあるページ](#a-page-with-a-bug)
- [ページを指定する](#choosing-the-page)
- [HTML レポート](#the-html-report)
- [短い要約](#a-short-summary)
- [コーディングエージェントで使う](#with-a-coding-agent)
- [次に読むもの](#where-to-go-next)

---

## <a id="before-you-start"></a>始める前に

Python 3.10 以上と、ブラウザーで開けるページ、つまり `.html` ファイルが入ったフォルダーが必要です。

```bash
pip install assay-ui
```

プロジェクトにビルド手順がある場合は、先にビルドしてから出力フォルダーをチェックしてください。assay がビルドを実行することはありません。

[すべてのインストール方法](install.ja.md)

---

## <a id="checking-a-page"></a>ページをチェックする

ページが入っているフォルダーを assay に指定します。

```console
assay ./my-app
```

初回の実行時には Chromium をダウンロードします。これは 1 回だけです。そのあと assay はフォルダーを localhost で配信し、Chromium で `index.html` を開き、ページが描画したコントロールをすべて一覧にし、そのコントロールからチェックを計画して、チェックを 1 件ずつ新しいタブで実行します。ほとんどのページは数秒から 1 分で終わります。

リポジトリには assay の評価に使っているページが入っているので、リポジトリをクローンすれば、このページの例をそのまま実行できます。次の例は、正常に動くクリックカウンターです。

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

## <a id="reading-the-result"></a>結果の読み方

最初の行は、assay が計画したチェックの数、実行できた数、成功した数と失敗した数を示します。それに続く各行は 1 件のチェックで、番号、結果、チェックの内容が並びます。

| 結果 | 意味 |
|---|---|
| `[ok]` | チェックを実行し、問題はありませんでした |
| `[FAILED]` | ページが自己矛盾しており（the page contradicts itself）、チェックの下の行がその内容を示します |
| `[not checked]` | assay がチェックを実行できませんでした。これが失敗として数えられることはありません |

終了コードは、失敗がなければ 0、チェックが 1 件でも失敗すれば 1、ページをまったくチェックできなければ 2 になるので、スクリプトから判定できます。

初回の実行時に Chromium をダウンロードすることを除けば、指定しない限りディスクには何も書き込みません。

---

## <a id="a-page-with-a-bug"></a>バグのあるページ

次の例は小さなお絵かきプログラムで、「Undo」の反応が 1 回分遅れます。

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

失敗しているのは C016 です。1 回目の「Undo」では何も起こらず、2 回目で処理が行われたので、「Undo」が 1 回分遅れていることがわかります。

1 つのバグが複数のチェックを失敗させた場合、最初の失敗がメッセージを表示し、残りは最初の失敗を指し示すので、メッセージを読むのは 1 回で済みます。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

assay はページが何のためのものかを知らないので、指摘（finding）は確認すべき箇所であって、確定したバグではありません。コントロールが、押された時点の状態では何もしないのが正しい場合もあります。

---

## <a id="choosing-the-page"></a>ページを指定する

```console
assay ./my-app                    # このフォルダーの index.html をチェック
assay ./my-app/todo.html          # 特定のページをチェック
assay ./my-app -e app.html        # またはフォルダー内のページを名前で指定
```

assay は、ローカルのフォルダーから配信したページを一度に 1 つチェックします。ビルドが必要なソースツリーを指定すると、実行すべきコマンドを教えてくれます。

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

## <a id="the-html-report"></a>HTML レポート

`--report` を付けると、各チェックの前後のページの様子を示す、開いて確認できるページが書き出されます。

```console
assay ./my-app --report out.html
```

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="タグフィルターに対する assay レポートのチェック 1 件です。タグを 2 回クリックすると見た目は元に戻りましたが、リストは絞り込まれたままでした。操作内容、理由、前後のページのスクリーンショットが表示されており、項目は 12 件から 1 件になっています。">

レポートは 1 つの HTML ファイルで、スクリーンショットはその隣の、レポートの名前を付けたフォルダーに入ります。この例では `out-shots` です。

---

## <a id="a-short-summary"></a>短い要約

`--one-line` を付けると、スクリプトやエージェント向けの短い要約を出力します。

```console
$ assay ./todo --one-line
assay: checked todo/index.html, 8 checks, nothing flagged.
```

問題があるときは、要約に指摘が 1 件ずつ並びます。重複する指摘は、メッセージを繰り返す代わりに最初の指摘を示します。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

---

## <a id="with-a-coding-agent"></a>コーディングエージェントで使う

assay には、コーディングエージェント向けのものが 2 つ付属しています。

**skill** はエージェントに対し、ページを書き終えたら assay を実行し、返答の最後に結果を載せるよう指示します。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**プラグイン**はフックを追加し、ページに変更があったターンの終わりに毎回チェックを自動で実行します。Claude Code では、次の 2 つのコマンドで skill とフックを一緒にインストールします。

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

どちらの方法でも、エージェントは assay が見つけた内容を報告するだけで、あなたが頼まない限り、それを理由にコードを変更することはありません。

[Harness](harnesses.ja.md) · [skill とプラグイン](../plugins/assay/README.ja.md)

---

## <a id="where-to-go-next"></a>次に読むもの

ドキュメントでは、すべてのオプションと Python API、assay が行うすべてのチェックとそれぞれが出力するメッセージ、コーディングエージェント向けの各 harness（エージェントの実行環境）でのセットアップを説明しています。

[ドキュメント](../README.ja.md#docs)

---

このページは [getting-started.md](getting-started.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
