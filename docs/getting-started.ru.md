<!-- i18n-source: docs/getting-started.md 588a51b0e5e0b00405a336f6847371a74e0ab7f9 -->

<h1 align="center">Начало работы</h1>

<p align="center"><a href="../README.ru.md">assay</a> › Начало работы</p>

<p align="center"><a href="getting-started.md">English</a> · <a href="getting-started.zh-CN.md">简体中文</a> · <a href="getting-started.ja.md">日本語</a> · <a href="getting-started.ko.md">한국어</a> · <b>Русский</b></p>

<p align="center">От установки assay до повседневного использования.</p>

---

## <a id="contents"></a>Содержание

- [Перед началом](#before-you-start)
- [Проверка страницы](#checking-a-page)
- [Как читать результат](#reading-the-result)
- [Страница с багом](#a-page-with-a-bug)
- [Выбор страницы](#choosing-the-page)
- [HTML-отчёт](#the-html-report)
- [Короткая сводка](#a-short-summary)
- [Работа с агентом для программирования](#with-a-coding-agent)
- [Что читать дальше](#where-to-go-next)

---

## <a id="before-you-start"></a>Перед началом

Вам нужен Python 3.10 или новее и страница, которую может открыть браузер, то есть папка с файлом `.html`.

```bash
pip install assay-ui
```

Если в вашем проекте есть этап сборки, сначала соберите проект, а затем проверьте папку с результатом сборки. assay никогда не запускает сборку сам.

[Все способы установки](install.ru.md)

---

## <a id="checking-a-page"></a>Проверка страницы

Укажите assay папку, в которой лежит ваша страница.

```console
assay ./my-app
```

При первом запуске скачивается Chromium, и это происходит один раз. Затем assay раздаёт папку через localhost, открывает `index.html` в Chromium, составляет список всех элементов управления (control), которые отрисовала страница, планирует по ним проверки (check) и запускает каждую проверку в новой вкладке. Большинство страниц проверяется за время от нескольких секунд до минуты.

В репозитории лежат страницы, по которым оценивают assay, поэтому в его клоне примеры с этой страницы можно запускать как есть. Вот счётчик нажатий, который работает.

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

## <a id="reading-the-result"></a>Как читать результат

Первая строка показывает, сколько проверок assay запланировал, сколько из них удалось выполнить, сколько пройдено и сколько не пройдено. Каждая следующая строка описывает одну проверку и содержит её номер, результат и то, что проверка сделала.

| Результат | Что он значит |
|---|---|
| `[ok]` | Проверка выполнена, и всё в порядке |
| `[FAILED]` | Страница противоречит сама себе (the page contradicts itself), и строка под проверкой объясняет, как именно |
| `[not checked]` | assay не смог выполнить проверку, и это никогда не считается провалом |

Код завершения равен 0, если ничего не провалено, 1, если не пройдена хотя бы одна проверка, и 2, если страницу вообще не удалось проверить, поэтому скрипт может на него опираться.

Помимо скачивания Chromium при первом запуске, assay ничего не записывает на диск, пока вы сами об этом не попросите.

---

## <a id="a-page-with-a-bug"></a>Страница с багом

Вот небольшая программа для рисования, в которой Undo срабатывает с опозданием на одно нажатие.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

Не пройдена проверка C016. Первое нажатие Undo ничего не сделало, а второе выполнило работу, поэтому Undo отстаёт на одно нажатие.

Если из-за одного бага проваливается несколько проверок, первая показывает сообщение, а остальные ссылаются на неё, поэтому сообщение достаточно прочитать один раз.

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

assay не знает, для чего нужна ваша страница, поэтому замечание (finding) указывает место, на которое стоит посмотреть, и не является подтверждённым багом. Элемент управления может правильно ничего не делать в том состоянии, в котором его нажали.

---

## <a id="choosing-the-page"></a>Выбор страницы

```console
assay ./my-app                    # проверить index.html в этой папке
assay ./my-app/todo.html          # проверить конкретную страницу
assay ./my-app -e app.html        # или указать страницу внутри папки
```

assay проверяет одну страницу за раз и раздаёт её из локальной папки. Если указать ему дерево исходного кода, которому нужна сборка, он подскажет, что запустить.

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

## <a id="the-html-report"></a>HTML-отчёт

`--report` записывает страницу, которую можно открыть в браузере. На ней для каждой проверки показано, как страница выглядела до и после.

```console
assay ./my-app --report out.html
```

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="Одна проверка из отчёта assay о фильтре
по тегам. Тег нажали дважды, он вернулся к прежнему виду, а список так и остался
отфильтрованным. Проверка показана вместе с её действиями, причиной и скриншотами страницы до
и после, на которых сначала двенадцать элементов, а потом один.">

Отчёт (report) состоит из одного HTML-файла, а скриншоты лежат рядом с ним в папке, названной по имени отчёта, здесь это `out-shots`.

---

## <a id="a-short-summary"></a>Короткая сводка

`--one-line` выводит короткую сводку для скриптов и агентов.

```console
$ assay ./todo --one-line
assay: checked todo/index.html, 8 checks, nothing flagged.
```

Если что-то не так, сводка перечисляет каждое замечание, а повтор называет первое замечание и не повторяет его сообщение.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

---

## <a id="with-a-coding-agent"></a>Работа с агентом для программирования

В assay есть две вещи для агентов для программирования (coding agent).

**Skill** велит агенту запустить assay, когда страница готова, и закончить ответ результатом.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**Плагин** (plugin) добавляет хук (hook), который автоматически запускает проверку в конце каждого хода (turn), изменившего страницу. В Claude Code эти две команды устанавливают skill и хук вместе.

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

В обоих случаях агент сообщает, что нашёл assay, и не меняет из-за этого код, если вы не попросите.

[Harness](harnesses.ru.md) · [Skill и плагин](../plugins/assay/README.ru.md)

---

## <a id="where-to-go-next"></a>Что читать дальше

Документация описывает все параметры и Python API, каждую проверку assay и сообщение, которое она выводит, а также настройку для каждого harness (среда запуска агента) для агентов программирования.

[Документация](../README.ru.md#docs)

---

Эта страница является переводом [getting-started.md](getting-started.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.
