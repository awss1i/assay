<!-- i18n-source: plugins/assay/README.md 228c8a685c996bdf309f1d30fcdd9410cff35811 -->

<h1 align="center">skill とプラグイン</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

---

<p align="center">エージェントが書いたばかりのページを、エージェント自身にチェックさせる 2 つの方法です。
<strong><a href="../../docs/harnesses.ja.md">15 種類の harness（エージェントの実行環境）へのインストール手順 →</a></strong></p>

---

## <a id="contents"></a>目次

- [skill](#the-skill)
- [プラグイン](#the-plugin)
- [報告のみ、修正はしない](#reporting-not-fixing)

---

## <a id="the-skill"></a>skill

skill は、対応している 15 種類の harness すべてで動作します。[`skills/checking-a-page/SKILL.md`](skills/checking-a-page/SKILL.md) は、ページを書き終えたら次のコマンドを実行するようエージェントに指示します。

```bash
assay <the page> --one-line
```

そして、その出力を一字一句そのまま返答の最後に載せるよう指示します。

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

問題がある場合は、次のようになります。

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

この 4 行は 1 つのバグによるものです。2 件目以降は、メッセージを繰り返す代わりに最初の指摘（finding）を示します。エージェントは assay の出力を要約せずにそのまま写すので、数値も文言も正確に保たれます。skill だけを使う場合、チェックをいつ実行するかはエージェントが判断します。

---

## <a id="the-plugin"></a>プラグイン

プラグインは `Stop` フックを追加します。このフックは、ページに変更があったターンの終わりに毎回チェックを実行します。Claude Code では、skill とフックが一緒にインストールされます。DeepSeek Harness は、Claude Code 用のブリッジを通じてフックだけを使います。

- **チェックするページ。** Web 関連のファイルが変更されると、同じフォルダーにあるページがチェック対象になります。そのため、`app.js` の編集も対象に含まれます。各フォルダーでは最も新しく変更された `.html` ファイルをチェックし、変更時刻が同じ場合は `index.html` を優先します。
- **探索の範囲。** フォルダーは最大 4 階層までたどり、`node_modules` と `.git` は飛ばします。前回の実行以降に変更されたファイルだけを対象にし、1 ターンでチェックするのは最大 3 ページです。
- **ページをチェックしたときは必ず報告します。** そのため、問題がなかったという結果を、assay が実行されなかったことと取り違えることはありません。ページを変更しなかったターンでは何も報告しません。
- **結果が見えるように、ターンを終了させずに続けます。** ただし、2 回続けてそうすることはありません。harness の `stop_hook_active` フラグを確認し、タイムスタンプを書き込みます（書き込み先は harness の一時フォルダー、それがなければ `.git/`、それもなければ `.assay-last-run` ファイルです）。タイムスタンプを書き込めない場合は、ターンを続けさせずに報告します。

---

## <a id="reporting-not-fixing"></a>報告のみ、修正はしない

エージェントは assay が見つけた内容を見せるだけで、あなたが頼まない限り、それを理由にコードを変更することはありません。assay はページが何のためのものかを知らないため、指摘は確認すべき箇所を示すものであって、バグと確定したものではありません。押されたときの状態ではコントロールが何もしないのが正しいこともあれば、値が意図的に制限されていることもあります。修正を頼めば、エージェントは修正します。

---

このページは [README.md](README.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
