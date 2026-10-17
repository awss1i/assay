<!-- i18n-source: docs/usage.md 3b28af15e7fcd3c1fba90ffdf0ef7cdc24513549 -->

<h1 align="center">assay の使い方</h1>

<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>

---

<p align="center">コマンドラインと Python から使える assay の機能をすべて紹介します。</p>

---

## <a id="contents"></a>目次

- [コマンド](#the-command)
- [実行例](#an-example)
- [HTML レポート](#the-html-report)
- [Python から使う](#from-python)

---

## <a id="the-command"></a>コマンド

```console
assay ./my-app                    # このフォルダーの index.html をチェック
assay ./my-app/todo.html          # 特定のページをチェック
assay ./my-app -e app.html        # またはフォルダー内のページを名前で指定

assay ./my-app --report out.html  # スクリーンショット付きの HTML レポートも書き出す
assay ./my-app --json             # 実行結果全体を JSON で出力
assay ./my-app --one-line         # スクリプトやエージェント向けの短い要約
assay ./my-app --surface          # 見つけたコントロールを一覧表示して終了
```

失敗が 1 つでもあれば終了コードは 0 以外になります。初回の実行時に Chromium をダウンロードすることを除けば、指定しない限りディスクには何も書き込みません。

---

## <a id="an-example"></a>実行例

assay には評価に使っているベンチマークのページが同梱されているので、今すぐそのどれかで試せます。次の例は小さなお絵かきプログラムで、「Undo」の反応が 1 回分遅れます。

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

失敗しているのは C016 です。1 回目の「Undo」では何も起こらず、2 回目で処理が行われたので、「Undo」が 1 回分遅れていることがわかります。

---

## <a id="the-html-report"></a>HTML レポート

`--report` を付けると、各チェックの前後のページの様子を示す、開いて確認できるページが書き出されます。

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="タグフィルターに対する assay レポートのチェック 1 件です。タグを 2 回クリックすると見た目は元に戻りましたが、リストは絞り込まれたままでした。操作内容、理由、前後のページのスクリーンショットが表示されており、項目は 12 件から 1 件になっています。">

---

## <a id="from-python"></a>Python から使う

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

---

このページは [usage.md](usage.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
