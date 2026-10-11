<!-- i18n-source: docs/how-it-works.md 5bf8fdf49caa9b6254f86f4d95b7b052a8547b2c -->

<h1 align="center">仕組み</h1>

<p align="center"><a href="how-it-works.md">English</a> · <a href="how-it-works.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="how-it-works.ko.md">한국어</a> · <a href="how-it-works.ru.md">Русский</a></p>

---

<p align="center">assay は、ページを実際のブラウザーで開き、ページ上のコントロールをすべて見つけ、計画した一連のチェックの中でそれぞれを操作し、各チェックの前後でページを比較します。assay はページが何のためのものかを知らないので、報告するのはページが自己矛盾している（the page contradicts itself）場合だけです。たとえば、ページがエラーを投げる、コントロールの反応が 1 回分遅れる、リストが空なのに件数が 1 と表示される、といった場合です。</p>

<p align="center">このページの前半では、1 回の実行の流れを説明します。後半ではチェックの種類ごとに、assay が何をするか、何を報告し、どんなメッセージを正確に出力するか、そしてどんなときに、なぜあえて報告しないのかを説明します。ここに載っているルールはすべて<a href="../bench/README.md">ベンチマーク</a>で検証しています。例外の多くは、より広く適用するルールが正常に動くページで誤検知（false alarm）を起こしたために設けたものです。</p>

---

## <a id="contents"></a>目次

- [1 回の実行の流れ](#how-a-run-goes)
  - [ページの配信](#serving-the-page)
  - [ページの読み込みを待つ](#waiting-for-the-page-to-load)
  - [コントロールを見つける](#finding-the-controls)
  - [チェックを計画する](#planning-the-checks)
  - [各チェックを実行する](#running-each-check)
  - [成功、失敗、未チェック](#passed-failed-or-not-checked)
  - [指摘をまとめる](#grouping-findings)
- [assay がチェックすること](#what-assay-checks)
  - [ページを開く](#opening-the-page)
  - [ボタンとリンクを押す](#pressing-buttons-and-links)
  - [入力欄に入力する](#typing-into-fields)
  - [フォームに入力して送信する](#filling-in-a-form-and-submitting-it)
  - [リストに項目を追加して削除する](#adding-items-to-a-list-and-removing-them)
  - [リストの件数や合計を表す数値](#numbers-that-count-or-total-a-list)
  - [保存と再読み込み](#saving-and-reloading)
  - [セル、チップ、カードを 2 回クリックする](#clicking-cells-chips-and-cards-twice)
  - [逆の働きをする対のボタン](#buttons-that-come-in-opposite-pairs)
  - [キャンバスに描画する](#drawing-on-a-canvas)
  - [描画した後にボタンを押す](#pressing-a-button-after-drawing)
  - [ゲームとアニメーションするキャンバス](#games-and-animated-canvases)
  - [ハンドルや行をドラッグする](#dragging-handles-and-rows)
  - [スライダー、チェックボックス、ドロップダウン、色、ファイル](#sliders-checkboxes-dropdowns-colours-and-files)
  - [タブと展開できるセクション](#tabs-and-expandable-sections)
  - [マークアップ上のラベルとラジオボタン](#labels-and-radio-buttons-in-the-markup)
  - [プレースホルダーが自身のパターンに合わない入力欄](#fields-whose-placeholder-fails-their-own-pattern)
  - [ページ上の NaN、undefined、[object Object]](#nan-undefined-and-object-object-on-the-page)
  - [何も反応しないページ](#a-page-where-nothing-responds)
- [assay がチェックできないこと](#what-assay-cant-check)

---

## <a id="how-a-run-goes"></a>1 回の実行の流れ

### <a id="serving-the-page"></a>ページの配信

assay はファイルを直接開くのではなく、フォルダーを localhost で配信します。`file://` で開いたページは JavaScript モジュールを読み込めないからです。

assay はビルドを決して実行しません。`npm install` は依存パッケージに含まれるスクリプトを何でも実行しますが、assay はまだ誰もレビューしていないコードを対象にしたツールだからです。ソースツリーを指定すると、自分で実行すべきコマンドを教えてくれます。

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

### <a id="waiting-for-the-page-to-load"></a>ページの読み込みを待つ

`load` イベントは、ほとんどのフレームワークが何かを描画する前に発火します。そのため assay は、`load` イベントも固定の待ち時間も使いません。ページ上のコントロールが変化しなくなるまで待ちます。

スピナーだけを表示しているページも、変化が止まっているという点では同じです。そのため、変化が止まった状態を準備完了とみなすのは、ページに操作できるものが現れてからです。そうしないと、*Loading…* のまま止まっているページが、コントロールのない完成したページに見えてしまいます。

---

### <a id="finding-the-controls"></a>コントロールを見つける

assay は、ブラウザーが描画するボタン、入力欄、ドロップダウン、キャンバス、リンクをすべて列挙し、それぞれについて CSS セレクター、ラベル、有効かどうか、サイズ、所属するフォームやコンテナーを記録します。

読み取るのは HTML のソースではなく、描画されたページです。JavaScript で作られたコントロールは対象に含まれ、`display: none`、`visibility: hidden`、`opacity: 0` やサイズ 0 で隠されたコントロールは含まれません。

HTML タグを見ただけではコントロールだとわからないものも見つけます。

| コントロール | assay が見分ける手がかり |
|---|---|
| ただの div で作られたグリッドのセル | `cursor: pointer` |
| 並べ替えできる表の見出し | `th` に付いた `cursor: pointer` |
| 編集可能な領域 | `contenteditable` |
| ドラッグハンドルやリサイズバー | `col-resize`、`move`、`grab`、`draggable` のいずれか |
| 隠れたボックスの上に描かれた星やスイッチ | 対応するラジオボタンやチェックボックスが隠れている、表示中の `label` |

JavaScript で追加されたクリックハンドラーは、ページから読み取れません。そのため、要素が何かをすることを示す手がかりは、マウスカーソルの形しかないことがよくあります。

---

### <a id="planning-the-checks"></a>チェックを計画する

assay は、見つけたコントロールからチェックの一覧を作ります。各チェックは 1 つ以上の操作からなります。たとえば、ボタンを 2 回押す、フォームに入力して送信ボタンを押す、などです。チェックの種類はすべて、このページの後半で説明します。

見た目が同じようなコントロール（グリッドのセルのように、種類、ラベル、サイズが同じもの）がページに多数ある場合、assay が使うのはそのうち最大 3 つです。それも先頭の 3 つではなく、グループ全体に散らばるように選びます。この仕組みを入れる前は、256 個のセルからなるグリッドを持つあるページで 505 件のチェックが計画され、増えた分のチェックはすべて同じことを報告していました。

---

### <a id="running-each-check"></a>各チェックを実行する

各チェックは新しいタブで、読み込みが終わったばかりのページから始まります。assay はチェックの前後で次のものを記録します。

- 各キャンバスで描画されたピクセル、その中心、平均色、ピクセル単位の正確なハッシュ
- 表示されているテキスト
- すべての入力欄の内容と、各ボックスにチェックが入っているかどうか
- ページ上の要素の数
- すべての要素のスタイルとクラスのハッシュ

WebGL のキャンバスは、アニメーションフレームの中で読み取ります。ほかのタイミングで読み取ろうとしても、その時点では内容がすでに消去されているからです。

`alert` は、ページの反応とみなします。*Length must be mm:ss*（長さは mm:ss 形式で入力してください）というアラートは、ページのほかの部分が何も変わらなくても、フォームが不正な入力を正しく拒否しているということです。`prompt` や `confirm` はページからの質問なので、それだけでは反応とみなしません。反応とみなすのは、その答えを受けてページが何をするかです。assay は `prompt` には妥当な値で答え、`confirm` はキャンセルせずに承認します。キャンセルすると、テスト対象の機能そのものが取り消されてしまうからです。

---

### <a id="passed-failed-or-not-checked"></a>成功、失敗、未チェック

チェックは、後述のルールのどれかに違反すると失敗し、そうでなければ成功します。まったく実行できなかったチェックは、失敗ではなく *not checked*（未チェック）として報告されます。

たとえば、生成されたある電卓は独自の `eval` 関数を定義しており、これが assay のページの読み取り方を壊します。assay は次のように報告します。

```
assay couldn't read this page, because the page replaces a built-in function that assay relies on (such as `eval` or `Function`). That doesn't mean the page is broken
```

このページは未チェックとして報告され、電卓自体は実際に正しく動きます。

チェック内の操作の 1 つをページが受け付けなかった場合（たとえば、*Press Space to start*（スペースキーで開始）のオーバーレイの裏に隠れたキャンバスはクリックできません）、チェックの残りの操作はそのまま続けます。これが原因でチェックが失敗するのは、操作が 1 つもできなかった場合だけで、そのときのメッセージは *couldn't*（できなかった）で始まります。

無効になっているコントロールは、ページが「今は使えません」と伝えているということです。assay はそのコントロールが無効だったことを記録し、反応がないことをページの不具合とはみなしません。25 と入力されると上限の 10 に丸めて `+` を無効にする数量の入力欄は、意図どおりに動いています。

---

### <a id="grouping-findings"></a>指摘をまとめる

1 つのバグが複数のチェックを失敗させた場合、最初の失敗にはメッセージが表示され、残りはその最初の失敗を参照します。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

そして要約の行には、そのうちいくつが重複かが表示されます。

```
18 cases planned, 18 carried out, 10 passed, 8 failed (7 of them repeat an earlier finding)
```

それでも失敗はすべて一覧に載り、数にも入ります。終了コードも変わりません。まとめることで変わるのは、出力の読みやすさだけです。

2 つの失敗がまとめられるのは、次の両方が当てはまる場合だけです。

- 同じルールに、同じメッセージで違反したこと（メッセージ中に引用された名前の違いは問いません）。
- 同じ場所にある同じ種類のコントロールで起きたこと。たとえば、1 つのタグバーのチップや、1 つのグリッドのセルです。ボタンのように名前を持つコントロールは名前も同じである必要があるため、「Undo」と「Redo」がまとめられることはありません。

クラッシュがまとめられるのは、エラーメッセージが同じで、同じコード行から投げられた場合だけです。

すべてのチェックが、読み込み中にすでにエラーを投げていたページで実行された場合、何も反応しないといったページ全体についての指摘（finding）には、そのことが示されます。

```
    ↳ the page threw an error while loading (C001), before anything was pressed
```

ベンチマークのページでのまとめ方はすべて、手書きの正解リスト（answer key）である [`bench/links.txt`](../bench/links.txt) と照合しています。

---

## <a id="what-assay-checks"></a>assay がチェックすること

以下の各セクションでは、まず assay がページに対して何をするか、次に何を報告するか、最後にどんなときになぜ報告しないかを説明します。1 つのチェックについての指摘には、`C001`、`C002` のように番号が付きます。どの 1 つのチェックでも示せない、実行全体についての指摘には `F001`、`F002` と番号が付き、ページ全体についての 2 つの指摘（何も反応しない、何も描画されない）は `C000` になります。

### <a id="opening-the-page"></a>ページを開く

最初のチェックでは、何も押さずにページを開き、落ち着くまで待ちます。

読み込み時やその後のどのチェックの最中でも、ページが捕捉されないエラーを投げると、assay はブラウザー自身のエラーメッセージを添えて報告します。

```
C001 [FAILED] open the page and let it settle
    → the page threw an error and stopped running, Cannot read properties of null (reading 'addEventListener')
```

同じエラーに遭遇したチェックはすべてそれを報告し、重複分は最初のものの下にまとめられます。

ページに何も表示されない場合、assay は次のように報告します。

```
    → the page shows nothing at all (no text, no images and nothing drawn), so there's nothing to test
```

このルールは、コンポーネントが `null` を返していた React アプリのために追加しました。そのアプリにはコントロールが 1 つもなかったため、チェックは「open the page」（ページを開く）の 1 件だけで、そのチェックは成功していました。空白のページが報告されるのは、使えるものが何もない場合か、反応を期待するチェック（フォームの送信など）の後も空白のままの場合だけです。描画するまでは空のキャンバスでしかないお絵かきツールは、読み込み時に空白だという理由では報告されません。

---

### <a id="pressing-buttons-and-links"></a>ボタンとリンクを押す

assay はすべてのボタンとリンクを 1 回押し、次に 2 回続けて押します。状態に関するバグは 2 回目に現れることが多いからです。たとえば、2 回目の「Start」、「Undo」の後の「Undo」、一方向にしか切り替わらないトグルなどです。また、先頭の 3 つのボタンを 2 つずつ組にして、両方の順序で押します（「Undo」の後に「Clear」、「Clear」の後に「Undo」）。ページによっては、一方の順序では正しく動き、もう一方では間違うことがあるからです。

これらのチェックで assay が報告するのは、ページが投げたエラーだけです。ボタンが何のためのものかは assay にはわからないので、ボタンが何かを変えることは求めません。選択状態を表示せずにブラシの色を設定するカラースウォッチは、見た目には何も変えませんが、壊れているわけではありません。目に見える変化を求めていた以前のバージョンは、正常に動くお絵かきツールで 21 件中 9 件のチェックを問題ありと判定していました。何が起きたかは "the visible text is unchanged"（表示テキストは変化していない）のような証拠として引き続き記録されますが、失敗としては扱いません。

まったく何もしないボタンも、次の 2 つの方法で検出されます。逆の働きをするボタンが正しく動いている場合（[対のボタン](#buttons-that-come-in-opposite-pairs)を参照）と、ページ全体で何も反応しない場合（[何も反応しないページ](#a-page-where-nothing-responds)を参照）です。

---

### <a id="typing-into-fields"></a>入力欄に入力する

assay は、すべてのテキスト入力欄に 4 種類の値を入力します。空の値、普通のテキスト（`Sample item`）、300 文字の文字列、そしてカンマ、引用符、HTML を含むテキストです。数値の入力欄には、空の値と数値を入力します。日付と時刻の入力欄（`date`、`time`、`datetime-local`、`month`、`week`）には、空の値と、その型として有効な値を入力します。入力した後、assay は入力欄からフォーカスを外すので、`change` イベントに反応するページもその入力を受け取れます。

これらのチェックで assay が報告するのは、ページが投げたエラーだけです。読み取り専用の入力欄は出力用なので、入力することはありません。パスワード生成ツールは、生成結果を読み取り専用の入力欄に書き込みます。

---

### <a id="filling-in-a-form-and-submitting-it"></a>フォームに入力して送信する

同じフォームまたはコンテナーの中で後ろにボタンがある入力欄ごとに、assay はそのフォームの入力欄をすべて埋めてから、そのボタンを押します。押す前には、フォーム内の各ラジオボタンのグループで最初の選択肢を選び、各ドロップダウンも変更します。評価やグループの選択が必須のフォームでは、それが未選択のまま送信を拒否するのが正しい動作だからです。

各入力欄には、その型が受け付ける値を入力します。メールアドレスの入力欄にはメールアドレス、`tel` の入力欄には電話番号、`url` の入力欄には URL、日付の入力欄には有効な日付です。ラベルを考慮するのはその後なので、*Phone* というラベルのテキスト入力欄には `555-0100` が、プレースホルダーが *mm:ss* の入力欄には `3:30` が入ります。

assay が何らかの変化を求めるのは、この種類のチェックだけです。入力を受け取り、送信ボタンを押されても、どこにも変化が見られないページは、入力を受け付けていません。

```
C007 [FAILED] type into Title, then press Add
    → nothing on the page changed at all
```

次の場合、assay はこれを報告しません。

- **ボタンがその入力欄のものではない場合。** 押すのは、同じフォームまたはコンテナーの中で入力欄の後ろにある最初のボタンだけです。ToDo リストの絞り込みボタン（「All」「Active」「Done」）は入力内容を無視するのが正しい動作で、入力欄とこれらのボタンを組み合わせたところ、正常に動く 3 つのリストを問題ありと判定してしまいました。Enter キーで追加する ToDo リストのように、後ろにボタンがない入力欄には、送信のチェックを一切行いません。
- **入力欄がキャンバスのページの設定項目である場合。** キャンバスのあるページでは、数値や日付の入力欄はたいていブラシサイズのような設定項目です。そのためページが反応することは求めず、代わりにキャンバスのチェックで判定します。
- **ページがアラートで応じた場合。** たとえば、フォームが不正な入力を拒否した場合です。
- **ボタンが無効になっている場合。**
- **ページが自ら停止している場合。** たとえば、終了したゲームです。ただし、何を押すべきかをページが示している場合は除きます（[ゲーム](#games-and-animated-canvases)を参照）。

---

### <a id="adding-items-to-a-list-and-removing-them"></a>リストに項目を追加して削除する

読み込んだ直後の ToDo リストには、入力ボックスとボタンしかありません。チェックボックス、各項目の横の「Delete」ボタン、残りの件数は、項目ができるまで存在しません。そこで、ページにフォームがある場合、assay はフォームに入力して 2 回送信し（2 回目は別の値を使います）、そのうえで現れたすべてのコントロールについてチェックを計画します。これらのチェックはどれも同じ 2 つの項目を追加するところから始まるので、チェック名の末尾は *with two saved*（2 件保存した状態で）になります。異なる 2 つの項目が必要なのは、間違った項目を削除してしまう「Delete」でも、項目が 1 つしかないとその誤りが表に出ないからです。

チェックで項目が削除されたのに、押したボタンが属する項目が残っている場合、assay は次のように報告します。

```
C014 [FAILED] press Remove, with two saved
    → this removed a row, but not the one it belongs to, and 'Another item https://example.com/other' is still there
```

テキストがまったく同じ項目は、どれが消えたのかを示せないので対象外にします。

実行の最後に assay は、フォームに入力した内容が、それによって作られた項目に表示されているかどうかも確認します。入力した値の一部が表示されていなければ、次のように報告します。

```
F001 [FAILED] values typed into a list show up in the new row
    → 'https://example.com/page' was typed in and accepted, but the new row in the list doesn't show it, first seen at C009
```

この確認はリストに対してだけ行います。ここでのリストとは、実行中に件数が変わったものすべてを指し、普通の表の行も含みます。確認はリストに項目が 2 つある状態で行います。項目が 1 つだと累計は入力した金額と等しくなり、合計を表示している行が正しく見えてしまうからです。次の場合、assay はこれを報告しません。

- **フォームがリストではない場合。** *Account created*（アカウントを作成しました）と表示し、メールアドレスもパスワードも表示しないサインアップフォームは正しい動作です。むしろパスワードは隠さなければなりません。
- **入力した値が 1 つも表示されていない場合。** 入力内容がまったく表示されない行は、1 つの入力欄が抜け落ちたのではなく、リストがまったく別のものを表示しているということです。
- **ページが 2 つ目の項目を拒否した場合。** ページが受け付けなかった値は、失われたとはみなしません。

---

### <a id="numbers-that-count-or-total-a-list"></a>リストの件数や合計を表す数値

実行の間ずっと、assay はページ上のすべての数値を、リストにある項目の数と合わせて読み取り、最後にそれらを比較します。

リストに合わせて 1 ずつ増減する数値は、リストの件数を数えています。したがって、リストが空なら 0 になるはずです。そうならない場合、assay は次のように報告します。

```
F002 [FAILED] the count of items matches the list
    → a number on this page goes up and down by one with the list, so it counts the list, but it shows 1 when the list is empty. It's +1 off at every size
```

この判定には、2 種類以上のリストの長さで、少なくとも 3 回読み取った値が必要です。また、使うのは整数だけです。小数は件数ではなく、測定値か金額だからです。一定の量だけずれていること自体は報告しません。一律の配送料を加える買い物かごは、中身に合わせて増減し、どの件数でも正しい値を示します。報告するのは、リストが空なのに 0 にならない件数だけです。

項目を追加するたびに変わる数値はリストに連動しているので、項目を削除したときにも変わるはずです。一度も変わらない場合、assay は次のように報告します。

```
F003 [FAILED] a total that follows the list also goes down
    → a number on this page changed every time the list grew (4 times) but never when it shrank (2 times), so it stops following the list when items are removed
```

これは、行を削除したときに合計を再計算しない支出管理アプリで起きる症状です。ここでは金額も対象にします。リストに連動すべき数値として最もよくあるのが累計だからです。条件は、リストが増える場面と減る場面の両方を観測していること、そして項目を追加するたびに毎回数値が変わっていることです。ときどきしか変わらない数値は、別の何かに連動しているからです。

---

### <a id="saving-and-reloading"></a>保存と再読み込み

2 つの項目を追加した後、assay は、ページがそれらを自身の `localStorage` または `sessionStorage` に書き込んだかどうかを確認します。書き込んでいれば、ページは次回もその項目が残っていると約束していることになります。そこで assay は 2 つの項目をもう一度追加し、ページを再読み込みして、項目がまだ表示されているかを確認します。消えていれば、次のように報告します。

```
C021 [FAILED] save two, reload, and they're still there
    → 'Sample item' and 'Another item' were saved in browser storage by the page, but are gone after reloading it
```

この確認を行うのは、ページが値を保存し、かつ再読み込みの前にその値を表示していた場合だけです。何も保存しないページに対しては、この確認は行いません。

---

### <a id="clicking-cells-chips-and-cards-twice"></a>セル、チップ、カードを 2 回クリックする

ボタンではないクリック可能な要素（グリッドのセル、タグのチップ、カード、星）は、1 回クリックし、次に 2 回続けてクリックします。また、最初の要素をクリックしてから、その隣の要素をクリックすることも行います。2 回クリックするときは、ページのほかの部分だけでなく要素そのものも監視します。操作の対象はその要素だからです。

1 回目のクリックでは要素が変化せず、2 回目で変化した場合、その要素の反応はクリック 1 回分遅れています。assay は次のように報告します。

```
C011 [FAILED] click Mon 9:00 twice
    → when clicked twice, this didn't change on the first click and did on the second, so it reacts one press late
```

このルールで、予約済みを表すスタイルが反転していたスケジューラーを検出できました。2 回目のクリックで変化したのが周りのページだけでなく、要素そのものである必要があります。画面上のキーボードのキーは、自分の見た目を変えません（押すたびに、別の場所にあるボードに文字が入力されます）。ボードの変化をキーの変化として読み取っていたときは、すべてのキーを反応が遅いと判定していました。

1 回目のクリックで要素が変化し、2 回目で元に戻ったのに、ページのほかの部分が元に戻らなかった場合、assay は次のように報告します。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
```

これは、タグの見た目はオフに戻ったのに、リストは絞り込まれたままになっているタグフィルターです。報告するのは、2 回目のクリックで変化したのが要素自身だけで、その外側が何も変化しなかった場合だけです。ツリー表示のフォルダーのうち、閉じるときに中のフォルダーも閉じるものは、2 回目のクリックで子要素と行数を描き直します。これはページが意図的に整理された状態を選んでいるので、報告しません。ライトボックスを開くサムネイルのように、どちらのクリックの後も見た目が同じ要素も報告しません。

これ以外の点では、これらのクリックはボタンを押した場合と同じように判定します。報告するのはエラーだけです。

---

### <a id="buttons-that-come-in-opposite-pairs"></a>逆の働きをする対のボタン

単独のボタンなら、目に見える変化がなくても構いません。説明がつかないのは、互いに逆の操作をする 2 つのボタンがあり、一方は毎回ページを変えるのに、もう一方は一度も変えない場合です。

assay はラベルから対を見つけます。対象は、ちょうど 1 単語だけが異なり、その単語が互いに反対の意味を持つ 2 つのラベルです（next と previous、forward と back、undo と redo、up と down、increase と decrease、more と less、plus と minus、add と remove または delete、expand と collapse）。assay はボタンを 2 つずつ組にして両方の順序で押すので、反応しない方のボタンも、相方の直後、つまり元に戻す対象があるときに押されることになります。一方が毎回ページを変え、もう一方が一度も変えなかった場合、assay は次のように報告します。

```
F001 [FAILED] Previous works as well as Next
    → Next changed the page, but Previous never did, even right after Next. As a pair, Previous should reverse what Next does
```

読み込んだ直後のデッキで「Previous」が何もしないのは正しい動作です。そのため、判定に使うのは「Next」の直後に押したときの結果です。

---

### <a id="drawing-on-a-canvas"></a>キャンバスに描画する

assay は、すべてのキャンバスに対して次の操作を行います。

- 4 か所をクリックします。クリック位置は、よくあるグリッドサイズでセルの境界を避けるように選んでいます。
- 同じ種類のプログラムを操作するときのやり方で使います。2 回クリックし、次に Space キー、右矢印キーと下矢印キー、Enter キーを押し、ドラッグします。
- 線を 1 本描き、次に別の場所にもう 1 本線を描きます。

1 本目の線が表示されたのに 2 本目が表示されなかった場合、キャンバスが描画を受け付けなくなっています。assay は次のように報告します。

```
C019 [FAILED] draw on canvas, then draw somewhere else on it
    → the first line drawn on this canvas appeared, but a second line drawn elsewhere did not, so the canvas stopped accepting drawing
```

これを報告する前に、2 本目の線は何か所かで試します。1 本目の線を無視したキャンバスについては、この確認自体を行いません。グラフはドラッグしても描画されませんが、最初から反応しないことで対象から外れます。このルールで、線を 1 本だけ描いて、その後の線をすべて何も言わずに無視するお絵かきツールを検出できました。計画にあるほかのチェックでは、この問題は見えませんでした。

キャンバスへのクリックでキャンバスが変化することを求めるのは、ページにほかに使えるものがない場合だけです。グラフは「Add」を押したときに描画されますし、ボールが跳ね回るキャンバスはボールを追加するまで空です。そのため、キャンバス自体に反応を求めていたときは、正常に動く 4 つのページを問題ありと判定していました。キャンバスしかないページで、キャンバスを操作してもキャンバスが変化しない場合、assay は次のように報告します。

```
    → the canvas this check clicked didn't change, even if other parts of the page did
```

その後もキャンバスに何も表示されない場合は、次のように報告します。

```
    → 1 canvas still shows nothing after every step of this check
```

実行の最後に、どのキャンバスにも単一の色以外何も表示されなかった場合、assay はページ全体についてこれを報告します。

```
C000 [FAILED] something appears on the canvas
    → nothing ever appeared on this canvas. 12 checks used the page, and the canvas stayed one flat colour through all of them, so whatever the program draws isn't reaching the screen
```

このルールで、座標変換によってすべての頂点がクリップされて消えていた 3 つの WebGL の立方体を検出できました。そのキャンバスは、全体が 1 色で塗られていて、何も描かれていないと測定されていました。これを報告するのは、少なくとも 2 件のチェックがページを操作し、ほかのチェックが 1 件も失敗しておらず、ページ上のすべてのコントロールに到達できた場合だけです。assay が到達できなかったコントロールが、描画を開始するコントロールかもしれないからです。

---

### <a id="pressing-a-button-after-drawing"></a>描画した後にボタンを押す

キャンバスのあるページでは、assay はボタンごとに、線を 2 本描いてからそのボタンを 2 回押します。どちらの押下も、assay が測定済みの状態から始まります。そのため、1 回目の押下で何も起きず、2 回目で何かが起きた場合、そのボタンは 1 回分遅れていることになります。

```
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
```

これは、変更の前ではなく後に状態を保存する Undo 履歴で起きる症状です。1 回目の「Undo」は、すでに画面に表示されている絵を復元します。線が 2 本必要なのは、履歴に線が 1 本しかないと両方の押下で何も起きず、不具合が見えないからです。読み込んだ直後のページではなく描画した後に確認するのは、操作対象のないコントロールが何もしないのは正しい動作だからです。

2 本目の線で何も描画されなかった場合は、代わりにチェックは成功となり、証拠には次のように記録されます。

```
the second line drew nothing, so there was no second step to undo
```

正しく動く「Undo」は、1 回目の押下をその空のステップに使います。これは 1 回分遅れているのとは違います。以前は、2 本目のストロークが描画されなかった正常なお絵かきツールが、このせいで「Undo」が遅れていると報告されていました。2 本目の線が描画されなかった場合でも、キャンバス自体は報告の対象になります（[キャンバスに描画する](#drawing-on-a-canvas)を参照）。

---

### <a id="games-and-animated-canvases"></a>ゲームとアニメーションするキャンバス

ひとりでに進むゲームのように、キャンバスが自分でアニメーションしている場合、assay はそれが止まるのを待ってから操作します。止まらない場合、キャンバス上の変化が assay の操作によるものかどうかを判断できないので、それらのチェックでは変化を求めません。

壁にぶつかったスネークゲームのように自ら停止したプログラムは、その後に押されたキーを無視しても報告しません。それはゲームが正しく動いているということです。例外は、何を押すべきかをページが示している場合です。*Press Space to restart*（スペースキーで再開）と表示しているのに Space キーを押しても何も変わらなければ、ページは自身の指示に反しています。assay は次のように報告します。

```
    → the page says to press Space, but pressing Space changes nothing
```

再開する手段のない終了したゲームは、それでも壊れているように見えることがあります。これは README の制限事項に記載しています。

---

### <a id="dragging-handles-and-rows"></a>ハンドルや行をドラッグする

分割ペインの仕切りや、ドラッグで並べ替える行は、クリックしても何も起きません。そこで assay は、それらをドラッグします。

- 各ドラッグハンドル（カーソルが `col-resize`、`move`、`grab` のもの）を 1 回ドラッグし、別のチェックでは 2 回ドラッグします。2 つ目のチェックで測定するのは 2 回目のドラッグだけです。仕切りの壊れ方として最も多いのが、1 回は動くのにその後はつかめなくなるというもので、2 回のドラッグをまとめて測定すると、1 回目の変化が 2 回目の失敗を覆い隠してしまうからです。
- `draggable` な各行は、本物の HTML5 ドラッグイベントを使って、リストのいちばん遠い端までドラッグします。いちばん遠い端にするのは、ほとんどのリストがドロップ先の手前に行を挿入するためです。隣の行にドロップすると行は元の位置に戻ってしまい、ドラッグできないリストのように見えていました。

ドラッグではページが変化することを期待します。変化しなければ、assay は次のように報告します。

```
C012 [FAILED] drag the divider, then drag it again
    → nothing on the page changed at all
```

---

### <a id="sliders-checkboxes-dropdowns-colours-and-files"></a>スライダー、チェックボックス、ドロップダウン、色、ファイル

assay は、すべてのスライダーを端まで動かし、すべてのチェックボックスとラジオボタンにチェックを入れ、すべてのドロップダウンで別の選択肢を選び、すべてのカラーピッカーを別の色に設定し、すべてのファイル入力に、受け付ける種類の小さなファイルを渡します。

これらのチェックで assay が報告するのは、ボタンと同じ理由で、ページが投げたエラーだけです。スライダーやチェックボックスが何を変えるはずなのかは、assay にはわからないからです。それでも、これらはページを操作したものとして数えます。[何も反応しない](#a-page-where-nothing-responds)かどうかのチェックには、この数が必要です。

---

### <a id="tabs-and-expandable-sections"></a>タブと展開できるセクション

どのチェックの間も、assay は画面上の各タブとセクション見出しを読み取ります。`aria-selected="true"` や `aria-expanded="true"` が付いたコントロールは、`aria-controls` で指定したパネルが表示されていることをスクリーンリーダーに伝えています。そのパネルがまったく描画されていなければ、ページは自己矛盾しています。assay は次のように報告します。

```
F001 [FAILED] the panel a selected tab or open section controls is shown
    → "Tab 2" is marked selected and controls the panel "panel-1", but that panel isn't shown, first seen at C004
```

空のパネルも、ページ上にボックスとして存在するので、表示されているとみなします。報告するのは、ブラウザーがまったく描画しないパネルだけです。

---

### <a id="labels-and-radio-buttons-in-the-markup"></a>マークアップ上のラベルとラジオボタン

どのチェックの間も、assay はラベルとラジオボタンがどう結び付いているかも読み取り、ページを見ただけではわからない次の 3 つの誤りを報告します。

- 1 つのグループにある 2 つのラジオボタンが同じ値を持っていて、どちらが選ばれたのかをフォームが区別できない場合。

  ```
  F002 [FAILED] labels and radio buttons are linked correctly
      → two radio buttons in the "option" group both have the value "2", so the form can't tell which of them was picked, first seen at C001
  ```

- `for` で存在しない id を指定しているラベルがある場合。

  ```
      → the label "Email" is linked to "emial", but nothing on the page has that id, first seen at C001
  ```

- 2 つのラベルが同じコントロールに結び付いていて、2 つ目のラベルが本来対象にしていたコントロールにラベルがない場合。

  ```
      → two labels are both linked to "star4", so one of them was meant for another control, which is left without a label, first seen at C001
  ```

---

### <a id="fields-whose-placeholder-fails-their-own-pattern"></a>プレースホルダーが自身のパターンに合わない入力欄

assay は、`pattern` とプレースホルダーの両方を持つ入力欄をすべて読み取ります。入力欄自身の入力例がその入力欄のパターンに合わなければ、入力例のとおりに入力した人は、その入力欄が必須のフォームを送信できません。

```
F001 [FAILED] the zip box accepts its own placeholder example
    → the placeholder shows "12345" as an example, but the pattern on this field, \d{5}, rejects it, so someone who types what the example shows can't submit a form that requires this field
```

これは入力して見つけるのではなく、マークアップから読み取ります。このルールのきっかけになった入力欄が、チェックでは到達できないウィザードの後半のステップにあったからです。スペースを含むプレースホルダーは、値の例ではなく *Enter five digits*（5 桁の数字を入力）のような説明文なので、対象外にします。

---

### <a id="nan-undefined-and-object-object-on-the-page"></a>ページ上の NaN、undefined、[object Object]

どのチェックの間も、assay は表示されているテキストとすべての入力欄から `NaN`、`undefined`、`[object Object]` を探します。これらを意図的に表示するページはありません。これらが表示されるのは、値が設定される前に使われたか、数値でないものから計算されたからです。assay は次のように報告します。

```
F001 [FAILED] no NaN, undefined or [object Object] on the page
    → the page shows `NaN` where a value should be, "Total: NaN". This usually means a value was used before it was set, or calculated from something that isn't a number, first seen at C008
```

assay 自身が数値ではないものを入力したチェックでは、これを報告しません。`Sample item` を渡された温度変換ツールが `NaN` を表示するのは、与えられた問いに対する正しい答えなので、正しい動作です。ここでは、空の入力欄は数値として扱います。

---

### <a id="a-page-where-nothing-responds"></a>何も反応しないページ

個々のチェックではボタンが何かをすることを求めないので、どのボタンも何の処理にもつながっていないページは、すべてのチェックを通過してしまいます。そこで assay は、実行の最後にページ全体を対象に確認します。コントロールが操作されたのに、ページ上で何も変化しなかった場合、次のように報告します。

```
C000 [FAILED] something on the page responds when used
    → nothing on the page changed after any control was used. 14 checks used what the page offers and none of them changed it, so the controls don't seem to be connected to any code
```

このルールで、3 つの「Add」ボタンがどれも何の処理にもつながっていなかったカンバンボードを検出できました。ページ全体が壊れていると判定するルールなので、報告するのは次の条件をすべて満たす場合だけです。

- 少なくとも 2 つの異なるコントロールが操作されたこと
- どのチェックでも、ページ上のどこにも変化が見られなかったこと
- assay がページ上のすべてのコントロールに到達したこと。以前、クリックできるセルは操作したものの、並べ替え用の見出しには到達しなかった並べ替え可能な表が、このように報告されたことがあります。その表は問題なく並べ替えができました。
- ページを開き直して、1 秒足らずではなく数秒の時間を与えることを 3 回繰り返しても、やはり何も起きないこと。「Retry」を押すと 2 秒かかる読み込みが始まるページは、1 回のチェックに与えられる時間内では、何も反応していないように見えます。

---

## <a id="what-assay-cant-check"></a>assay がチェックできないこと

assay はコントロールが何をするためのものかを知らないので、動きはするものの間違った処理をするページ（たとえば合計の計算を間違えるページ）は、たいていチェックを通過します。コントロールがすべき動作を確かめるには、受け入れ基準（acceptance criteria）を書いて Python から渡してください。`check(folder, criteria=[...])` は、それぞれ独自の操作と期待される結果を持つケースを受け取り、その期待を書かれたとおりにチェックします。

---

このページは [how-it-works.md](how-it-works.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
