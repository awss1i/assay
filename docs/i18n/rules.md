<h1 align="center">Translating the Docs</h1>

---

<p align="center">The docs that explain how to use assay are kept in English, Simplified Chinese,
Japanese, Korean and Russian. English is the source. This page is the convention every translation
follows, and <a href="glossary.md">glossary.md</a> fixes the word used for each of assay's own
terms in each language.</p>

---

## Contents

- [What Is Translated](#what-is-translated)
- [File Names](#file-names)
- [The Language Switcher](#the-language-switcher)
- [Headings and Anchors](#headings-and-anchors)
- [What Stays in English](#what-stays-in-english)
- [Links](#links)
- [Writing](#writing)
- [Keeping Translations Current](#keeping-translations-current)
- [The Closing Note](#the-closing-note)

---

## What Is Translated

These docs have a translation in each of the four languages:

- `README.md`
- `docs/usage.md`
- `docs/harnesses.md`
- `docs/how-it-works.md`
- `plugins/assay/README.md`

These stay in English only, because issues, pull requests and security reports happen in
English, or because a program reads or writes them:

- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` and `plugins/assay/SECURITY.md`
- the pull request template and the issue forms in `.github/`
- `plugins/assay/skills/checking-a-page/SKILL.md`, which a coding agent reads
- the benchmark READMEs, which `bench/score.py` and `bench/planted/score.py` rewrite
- this page and the glossary

To translate another doc, add all four translations in the same change and list it above.

---

## File Names

A translation sits next to its English source, with the language code before `.md`:

| Language | Code | Example |
|---|---|---|
| Simplified Chinese | `zh-CN` | `docs/usage.zh-CN.md` |
| Japanese | `ja` | `docs/usage.ja.md` |
| Korean | `ko` | `docs/usage.ko.md` |
| Russian | `ru` | `docs/usage.ru.md` |

Because a translation is in the same folder as its source, relative links and image paths work
unchanged.

---

## The Language Switcher

Every translated doc and its English source carry the same switcher, a centred line directly
under the title. The current language is bold and unlinked, the others are links, and the order
is always English, 简体中文, 日本語, 한국어, Русский. In `docs/usage.md` it looks like this.

```html
<p align="center"><b>English</b> · <a href="usage.zh-CN.md">简体中文</a> · <a href="usage.ja.md">日本語</a> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>
```

In `docs/usage.ja.md` the same line reads like this.

```html
<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="usage.ko.md">한국어</a> · <a href="usage.ru.md">Русский</a></p>
```

`README.md` is the one exception. PyPI shows it as the project description, where relative links
don't resolve, so its switcher links are full GitHub URLs, like
`https://github.com/awss1i/assay/blob/main/README.zh-CN.md`. The translated READMEs aren't on
PyPI, so their switchers use relative links like every other doc.

---

## Headings and Anchors

Every heading below the title is translated, and starts with an anchor that carries the id GitHub
gives the English heading. For example, `## The command` in English becomes this in Chinese.

```markdown
## <a id="the-command"></a>命令
```

The id is the English heading in lowercase, with spaces turned into hyphens and punctuation
removed, so `## Everywhere Else: The Skill on Its Own` gets `everywhere-else-the-skill-on-its-own`.
In-page links, the centred nav and the Contents lists keep the English fragment, like
`#the-command`, so the same link works in all five languages. A translation has the same headings
in the same order as its source, and the test checks that.

---

## What Stays in English

Keep these exactly as they are in the source:

- code blocks, except the explanatory `#` comments inside them
- commands, flags, file paths, environment variables, URLs and anything else in backticks
- anything assay prints, such as a check line, a message or the `--one-line` summary
- product and project names, like assay, Playwright, Chromium, Python, PyPI, GitHub and the harness names
- acronyms, like CLI, DOM, LLM, QA, HTML, JSON, API and UI
- badges, and the images themselves

Translate everything else, including headings, image alt text, link text, the labels in the
centred nav, and `#` comments in code blocks.

When prose quotes something assay prints, keep the English so a reader can match it to their
terminal, and give its meaning in parentheses right after it.

The first time a doc uses one of assay's own terms, give the English in parentheses after the
translation, like `误报（false alarm）`. After that, use the translation alone.
[glossary.md](glossary.md) lists the word to use for each term in each language.

---

## Links

A link to a doc that has a translation points to the translation in the same language. A link to
an English-only doc stays as it is. Keep the link's form and change only the file name, so a full
GitHub URL stays a full URL and a relative link stays relative.

---

## Writing

In every language, write the way the English is written, in plain, direct sentences that say who
does what. Don't use dashes of any kind, including the Chinese double dash and the Japanese
horizontal bar. Use a colon only to introduce a list, and don't join clauses with a semicolon.

**Simplified Chinese.**

- Put one half-width space between Chinese and Latin letters, digits or inline code, like
  `运行 assay 检查 3 个页面`.
- Use full-width punctuation in prose, like `，。（）「」`, and half-width punctuation inside code.
- Address the reader as 你, never 您.

**Japanese.**

- Write in です/ます.
- Use katakana for general technical words, like ブラウザー and リポジトリ.
- Put a half-width space between Japanese and Latin letters, digits or inline code, like
  `API キー` and `` `pip` でインストール ``.
- Use full-width `、。` in prose, and 「」 around a UI label.

**Korean.**

- Use 합니다 for statements and 하세요 for instructions. Never address the reader as 당신.
- Write general technical words in Hangul, like 브라우저 and 저장소, and keep product names in
  English.
- Attach particles directly to Latin words and code, like `assay를` and `` `pip`로 ``.

**Russian.**

- Address the reader as вы, in lowercase, and give instructions in the plural imperative, like
  `Установите`.
- Write ё wherever it belongs, like `ещё` and `всё`.
- Use «» as quotation marks in prose. Straight quotes appear only inside code.
- Where Russian would join two nouns with a dash, write a verb like `является` instead, as in
  `assay является CLI`, or rephrase the sentence, because the no-dash rule applies here too.
- Capitalise only the first word of a heading.
- Write decimals in prose with a comma, like `3,9 минуты`, and keep the point inside code and in
  anything assay prints.
- For Git and GitHub words, use the loanwords in the
  [Web Standards dictionary](https://github.com/web-standards/dictionary/blob/main/git.md), like
  коммит, форк, пулреквест and ишью. Ишью is neuter and never declined.

---

## Keeping Translations Current

The first line of every translation records which version of its English source it was made
from, like this.

```html
<!-- i18n-source: docs/usage.md 3f1c0d9e5a7b2c4d6e8f0a1b3c5d7e9f1a2b4c6d -->
```

The long hex number is the git blob id of the source file. `tests/test_translations.py` compares
it with the source as it is now, and fails when the English has changed since the translation was
made. It also fails when a translation's headings don't match its source, or when a translated doc
is missing one of the four languages.

When the English changes:

1. See what changed with `git diff <id> HEAD:docs/usage.md`, using the id from the translation's
   first line.
2. Update the matching part of all four translations.
3. Record the new version with
   `python docs/i18n/stamp.py docs/usage.zh-CN.md docs/usage.ja.md docs/usage.ko.md docs/usage.ru.md`.

Commit the English change and its translations together.

---

## The Closing Note

Each translation ends with a divider and this note, naming and linking its source:

- 简体中文: `本文是 [usage.md](usage.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。`
- 日本語: `このページは [usage.md](usage.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。`
- 한국어: `이 문서는 [usage.md](usage.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.`
- Русский: `Эта страница является переводом [usage.md](usage.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.`
