<!-- i18n-source: docs/usage.md 4fc8af90f6d6d12babc4d55ec7e9668ec62ae3d8 -->

<h1 align="center">使い方</h1>

<p align="center"><a href="../README.ja.md">assay</a> › 使い方</p>

<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>

<p align="center">assay コマンドのすべてのオプション、出力、終了コード、HTML レポート、Python API を説明します。</p>

---

## <a id="contents"></a>目次

- [コマンド](#the-command)
- [オプション](#options)
- [assay の出力](#what-assay-prints)
  - [標準の出力](#the-default-output)
  - [短い要約](#the-short-summary)
  - [JSON](#json)
  - [コントロールの一覧](#the-controls)
- [終了コード](#exit-codes)
- [HTML レポート](#the-html-report)
- [色](#colour)
- [エラー](#errors)
- [Python から使う](#from-python)
  - [ページをチェックする](#checking-a-page)
  - [受け入れ基準](#acceptance-criteria)
  - [コントロールを一覧にする](#listing-the-controls)

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

assay はパスを 1 つ受け取ります。パスがフォルダーの場合、assay はそのフォルダーを配信し、中の `index.html` を開きます。パスが `.html`、`.htm`、`.xhtml` のいずれかで終わる場合は、そのファイルがチェックするページになります。ページは隣にあるファイルを読み込むので、assay はそのファイルが入っているフォルダーを配信します。

失敗が 1 つでもあれば終了コードは 0 以外になります。初回の実行時に Chromium をダウンロードすることを除けば、指定しない限りディスクには何も書き込みません。

---

## <a id="options"></a>オプション

| オプション | 動作 |
|---|---|
| `-e ENTRY`, `--entry ENTRY` | フォルダー内の `index.html` の代わりに `ENTRY` を開きます |
| `--report FILE` | 各チェックの前後のページのスクリーンショットを含む HTML レポートを `FILE` にも書き出します |
| `--json` | 標準の出力の代わりに、実行全体を JSON で出力します |
| `--one-line` | 何をチェックし、何を問題ありと判定した（flagged）かの短い要約を出力します |
| `--if-page` | パスが assay でチェックできるページでなければ、何も出力せずに 0 で終了します |
| `--surface` | ページにあるコントロールを出力して終了し、チェックは実行しません |
| `--version` | インストールされているバージョンを出力して終了します |
| `-h`, `--help` | オプションの説明を出力して終了します |

`--if-page` は、編集のたびに実行されるフック向けのオプションです。ほとんどの編集はページに対するものではないので、このオプションを付けると、assay はそうした場合にエラーをエージェントの会話に出力せず、何も出力しません。

`--json` と `--one-line` を両方指定した場合、assay は JSON を出力します。

---

## <a id="what-assay-prints"></a>assay の出力

### <a id="the-default-output"></a>標準の出力

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

最初の行は、計画したチェック、実行したチェック、成功したチェック、失敗したチェックの数を示します。そのあとに、すべてのチェックが実行した順に、番号、結果、チェックの内容とともに並びます。

| 結果 | 意味 |
|---|---|
| `[ok]` | チェックを実行し、問題はありませんでした |
| `[FAILED]` | ルールに違反しており、`→` で始まる行が何が起きたかを示します |
| `[not checked]` | チェックを実行できませんでした。これが失敗として数えられることはありません |

前の指摘（finding）と重複する失敗は、メッセージの代わりに `↳ same finding as C003`（C003 と同じ指摘）と表示され、最初の行は失敗のうち何件が重複かを示します。

チェックには、`C001`、`C002` のように番号が付きます。どの 1 つのチェックでも示せない、実行全体についての指摘には `F001`、`F002` と番号が付き、ページ全体についての 2 つの指摘は `C000` になります。

---

### <a id="the-short-summary"></a>短い要約

問題がなければ、`--one-line` は 1 文を出力します。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

問題があるときは、指摘 1 件につき 1 行を出力します。重複する指摘は、メッセージを繰り返す代わりに最初の指摘を示します。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

実行できなかったチェックがある場合は、最初の行がその件数を示すので、実行されなかったチェックのせいでページが問題なしと報告されることはありません。ページ由来のテキストは、表示可能な文字だけの 1 行にまとめられるので、ページが要約に独自の行を追加することはできません。

---

### <a id="json"></a>JSON

`--json` は、次のフィールドを持つオブジェクトを 1 つ出力します。

| フィールド | 内容 |
|---|---|
| `version` | assay のバージョン |
| `entry` | 開いたページ |
| `planned`, `passed`, `failed` | 計画したチェック、成功したチェック、失敗したチェックの数 |
| `works` | 失敗したチェックがなければ `true` |
| `sandboxed` | ページが Chromium のサンドボックス内で動いた場合は `true` |
| `surface` | 見つかったすべてのコントロール。それぞれの `kind`、`selector`、`label` と、`enabled` かどうかを含みます |
| `cases` | すべてのチェック。下で説明します |
| `links` | 指摘どうしのすべての関連。`from`、`kind`、`to`、`why` を含みます |
| `console_errors` | ページがコンソールに出力したエラー |
| `failed_requests` | ページが送信して失敗したリクエスト |

`cases` の各項目は、次のフィールドを持ちます。

| フィールド | 内容 |
|---|---|
| `id` | チェックの番号。たとえば `C003` |
| `what` | チェックの内容を言葉で表したもの |
| `outcome` | `passed`、`failed`、`unknown` のいずれか。`unknown` は未チェックを意味します |
| `detail` | 失敗したチェックで、何がうまくいかなかったか |
| `measured` | チェックが成功したか失敗したかにかかわらず、assay が測定した内容 |
| `acts` | チェックが順に実行した操作 |
| `rules` | チェックが違反したルールの名前 |
| `key` | チェックを追加しても変わらない指摘の名前。形式は `rule@what the check did` です |
| `links` | この指摘から別の指摘への関連。`kind`、`to`、`why` を含みます |

コンソールのエラーや失敗したリクエストでチェックが失敗することはありません。ページはエラーを出力したりアイコンが欠けたりしていても、正常に動くことがあるからです。ただし、チェックが実際に失敗したときには、最初に読む価値があることが多い情報です。

---

### <a id="the-controls"></a>コントロールの一覧

`--surface` は、assay がページで見つけたものを 1 行に 1 つのコントロールとして、種類、セレクター、ラベル、ピクセル単位のサイズとともに一覧にします。

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter --surface
kind: page
- button `#inc` 'Increment' 151x52
- button `#reset` 'Reset' 107x52
```

---

## <a id="exit-codes"></a>終了コード

| コード | 条件 |
|---|---|
| 0 | 失敗したチェックがない |
| 1 | 少なくとも 1 件のチェックが失敗した |
| 2 | ページが存在しない、ビルドが必要、または Chromium をインストールできなかったため、ページをチェックできなかった |

`--if-page` を付けた場合、assay は 2 ではなく 0 で終了します。`--surface` は、コントロールを一覧にしたあと 0 で終了します。

---

## <a id="the-html-report"></a>HTML レポート

`--report` を付けると、各チェックの前後のページの様子を示す、開いて確認できるページが書き出されます。

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="タグフィルターに対する assay レポートのチェック 1 件です。タグを 2 回クリックすると見た目は元に戻りましたが、リストは絞り込まれたままでした。操作内容、理由、前後のページのスクリーンショットが表示されており、項目は 12 件から 1 件になっています。">

レポートは、チェックごとに、操作内容、結果と理由、assay が測定した内容を示します。レポートは 1 つの HTML ファイルで、スクリーンショットはその隣の、レポートの名前を付けたフォルダーに入ります。そのため `--report out.html` は `out-shots/` も書き出します。レポートはインターネットから何も読み込まないので、ディスクや CI の成果物からそのまま開けます。また、ライトテーマとダークテーマのどちらにも従います。

---

## <a id="colour"></a>色

ターミナルでは、失敗が目立つように assay が結果に色を付けます。パイプやファイルに送る出力には色が付きません。環境変数 `NO_COLOR` を設定すると色が無効になり、`FORCE_COLOR` を設定するとどこでも色が有効になります。

---

## <a id="errors"></a>エラー

assay は、次のメッセージをエラー出力に出力します。

| メッセージ | 意味 |
|---|---|
| `assay: my-app/index.html doesn't exist` | パスに、開けるページがありません |
| `assay: index.html loads /src/main.jsx, which a browser can't run without a build step.` | フォルダーがソースツリーです。assay は自分で実行すべきビルドコマンドを出力し、assay がそれを実行することはありません |
| `assay: index.html loads /src/main.jsx, which a browser can't run, but dist/index.html is built.` | フォルダーにビルド済みのコピーがあり、assay は代わりにチェックすべきパスを出力します |
| `assay: there's no index.html here, but there's a package.json, so the page probably comes from a build step.` | フォルダーが、まだビルドされていないプロジェクトです |
| `assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.` | 初回の実行で Chromium をダウンロードしています |
| `assay: playwright isn't installed. Run pip install assay-ui to install it.` | この Python に assay 自身の依存パッケージがありません |
| `assay: Chromium's sandbox couldn't start on this system, so the page ran without it.` | ページのチェックは行われました。root として実行した場合や一部のコンテナでは、サンドボックスを起動できません |

1 件のチェックを実行できなかった場合でも実行は続き、そのチェックは理由とともに未チェック（not checked）として報告されます。たとえば、assay が利用している組み込み関数をページが置き換えている場合です。

---

## <a id="from-python"></a>Python から使う

### <a id="checking-a-page"></a>ページをチェックする

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

`check` は、次の引数を受け取ります。

| 引数 | 動作 |
|---|---|
| `folder` | ページが入っているフォルダー、またはページそのもの。コマンドがパスを読むのと同じように解釈します |
| `entry` | フォルダー内で開くページ。既定値は `index.html` です |
| `criteria` | assay のチェックの前に実行する、自分で書いたチェック。下で説明します |
| `shots` | 各チェックの前後のスクリーンショットを保存するフォルダー。指定しなければ、ディスクには何も書き込みません |

戻り値は、次の属性を持つレポートです。

| 属性 | 内容 |
|---|---|
| `works` | 失敗したチェックがなければ `True` |
| `plan` | 実行した順に並んだすべてのチェック |
| `results` | 各チェックの結果。チェックの番号がキーです |
| `failing` | 失敗した結果。自分で書いた基準が先に並びます |
| `unchecked` | 実行できなかったチェックの結果 |
| `surface` | assay が見つけたコントロール |
| `console_errors`, `failed_requests` | ページが出力したエラーと、失敗したリクエスト |
| `summary()`, `render()` | 出力の最初の行と出力全体。どちらもテキストです |

各結果は、実行した `case`、`"passed"`、`"failed"`、`"unknown"` のいずれかである `outcome`、何がうまくいかなかったかを示す `detail`、assay が測定した `evidence`、違反した `rules`、そして `key` を持ちます。

---

### <a id="acceptance-criteria"></a>受け入れ基準

assay はコントロールが何をするためのものかを知らないので、動作はするものの間違ったことをするページは、たいていチェックを通過します。ページがすべきことをチェックするには、自分でチェックを書き、受け入れ基準（acceptance criteria）として渡します。

```python
from assay import Case, check

total = Case(
    id="A001",
    what="adding 10 and 20 shows a total of 30",
    acts=[{"fill": "#price=10"}, {"click": "#add"},
          {"fill": "#price=20"}, {"click": "#add"}],
    expect={"want": "Total: 30"},
    origin="criterion",
)

report = check("./my-app", criteria=[total])
```

合計の計算が間違っているページでは、この基準は次の説明とともに失敗します。

```
the page doesn't contain 'Total: 30'
```

`acts` は、順に実行する操作です。それぞれの操作は、動詞とその対象からなります。

| 操作 | 動作 |
|---|---|
| `{"click": "#add"}` | セレクターに一致する要素をクリックします。`{"click": "Add"}` のように、コントロール上の文字も使えます |
| `{"fill": "#price=10"}` | `=` のあとの値を、セレクターに一致する入力欄に入力します |
| `{"press": "Enter"}` | キーを押します |
| `{"reload": "page"}` | ページを再読み込みします |
| `{"wait": "2"}` | 指定した秒数だけ待ちます。上限は 10 秒です |

`expect` は、そのあとに成り立つべきことを示します。

| 期待 | 成り立つべきこと |
|---|---|
| `{"want": "Total: 30"}` | そのテキストがページに表示される |
| `{"unchanged": True}` | ページが元のまま変わらない |
| `{"quiet": True}` | 特に条件はありません。チェックが失敗するのは、ページがエラーを投げた場合だけです |
| `{}` | ページのどこかが変化する |

assay はすべてのチェックに自分で番号を付けるので、基準の `id` は結果では置き換えられます。`--json` は assay が計画したすべてのチェックの `acts` を出力するので、assay がそれぞれの操作をどう書くかがわかります。

---

### <a id="listing-the-controls"></a>コントロールを一覧にする

`look` は、`--surface` と同じように、チェックを実行せずにページを開いてコントロールを一覧にします。

```python
from assay import look

opened = look("./my-app")
print(opened.surface.render())
```

---

このページは [usage.md](usage.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
