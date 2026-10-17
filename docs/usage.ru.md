<!-- i18n-source: docs/usage.md 3b28af15e7fcd3c1fba90ffdf0ef7cdc24513549 -->

<h1 align="center">Использование assay</h1>

<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <a href="usage.ja.md">日本語</a> · <a href="usage.ko.md">한국어</a> · <b>Русский</b></p>

---

<p align="center">Всё, что assay умеет делать из командной строки и из Python.</p>

---

## <a id="contents"></a>Содержание

- [Команда](#the-command)
- [Пример](#an-example)
- [HTML-отчёт](#the-html-report)
- [Использование из Python](#from-python)

---

## <a id="the-command"></a>Команда

```console
assay ./my-app                    # проверить index.html в этой папке
assay ./my-app/todo.html          # проверить конкретную страницу
assay ./my-app -e app.html        # или указать страницу внутри папки

assay ./my-app --report out.html  # также записать HTML-отчёт со скриншотами
assay ./my-app --json             # вывести весь запуск в формате JSON
assay ./my-app --one-line         # краткая сводка для скриптов и агентов
assay ./my-app --surface          # перечислить найденные элементы управления и завершиться
```

Если что-то не прошло, код завершения будет ненулевым. Помимо скачивания Chromium при первом
запуске, assay ничего не записывает на диск, пока вы сами об этом не попросите.

---

## <a id="an-example"></a>Пример

assay поставляется вместе со страницами бенчмарка, по которым его оценивают, поэтому вы можете
прямо сейчас запустить его на одной из них. Вот небольшая программа для рисования, в которой Undo
срабатывает с опозданием на одно нажатие.

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

Не пройдена проверка (check) C016. Первое нажатие Undo ничего не сделало, а второе выполнило
работу, поэтому Undo отстаёт на одно нажатие.

---

## <a id="the-html-report"></a>HTML-отчёт

`--report` записывает страницу, которую можно открыть в браузере. На ней для каждой проверки
показано, как страница выглядела до и после.

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="Одна проверка из отчёта assay о фильтре
по тегам. Тег нажали дважды, он вернулся к прежнему виду, а список так и остался
отфильтрованным. Проверка показана вместе с её действиями, причиной и скриншотами страницы до
и после, на которых сначала двенадцать элементов, а потом один.">

---

## <a id="from-python"></a>Использование из Python

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

---

Эта страница является переводом [usage.md](usage.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.
