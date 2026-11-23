<!-- i18n-source: docs/install.md c51339dcc8b0355b209153fdf0186ea21a55095f -->

<h1 align="center">Установка</h1>

<p align="center"><a href="../README.ru.md">assay</a> › Установка</p>

<p align="center"><a href="install.md">English</a> · <a href="install.zh-CN.md">简体中文</a> · <a href="install.ja.md">日本語</a> · <a href="install.ko.md">한국어</a> · <b>Русский</b></p>

<p align="center">Все способы установить assay.</p>

---

## <a id="contents"></a>Содержание

- [pip](#pip)
- [uv](#uv)
- [pipx](#pipx)
- [Chromium](#chromium)
- [Обновление](#updating)
- [Удаление](#uninstalling)
- [Агенты для программирования](#coding-agents)

---

## <a id="pip"></a>pip

```bash
pip install assay-ui
```

assay нужен Python 3.10 или новее. Пакет называется `assay-ui`, а команда, которую он
устанавливает, называется `assay`. Если команда `pip` не найдена, используйте
`python3 -m pip install assay-ui`.

---

## <a id="uv"></a>uv

```bash
uv tool install assay-ui
```

Если в системе нет Python 3.10 или новее, uv скачает Python для assay и добавит команду `assay`
в ваш `PATH`.

---

## <a id="pipx"></a>pipx

```bash
pipx install assay-ui
```

pipx устанавливает assay в отдельное изолированное окружение, отдельно от остальных ваших
пакетов Python.

---

## <a id="chromium"></a>Chromium

assay открывает страницы в Chromium через Playwright. При первом запуске assay проверяет,
установлен ли Chromium, и скачивает его, если его нет. Перед началом скачивания assay выводит
это сообщение.

```
assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.
```

При установке через pip Chromium можно скачать заранее, например при сборке образа контейнера.

```bash
python -m playwright install chromium
```

В Linux для Chromium нужны некоторые системные библиотеки. Если первый запуск не удался, потому
что одной из них нет, эта команда установит их вместе с Chromium.

```bash
python -m playwright install --with-deps chromium
```

---

## <a id="updating"></a>Обновление

| Способ установки | Команда |
|---|---|
| pip | `pip install --upgrade assay-ui` |
| uv | `uv tool upgrade assay-ui` |
| pipx | `pipx upgrade assay-ui` |

`assay --version` выводит установленную версию.

---

## <a id="uninstalling"></a>Удаление

| Способ установки | Команда |
|---|---|
| pip | `pip uninstall assay-ui` |
| uv | `uv tool uninstall assay-ui` |
| pipx | `pipx uninstall assay-ui` |

После удаления assay Chromium остаётся в кеше Playwright. При установке через pip выполните
`python -m playwright uninstall` до удаления assay, и Playwright удалит скачанные им браузеры.

---

## <a id="coding-agents"></a>Агенты для программирования

И skill, и плагин (plugin) запускают команду `assay`, поэтому сначала установите assay одной из
команд выше. Дальше у каждого harness (среда запуска агента) свои шаги.

| Harness | Что устанавливается |
|---|---|
| [Claude Code](harnesses.ru.md#claude-code) | Skill и хук (hook), в виде плагина |
| [Codex](harnesses.ru.md#codex) | Skill и хук (hook), в виде плагина |
| [Grok Build CLI](harnesses.ru.md#grok-build-cli) | Skill и хук (hook), в виде плагина |
| [Cursor](harnesses.ru.md#cursor) | Skill, в виде плагина |
| [DeepSeek Harness](harnesses.ru.md#deepseek-harness) | Skill в виде скопированного файла и хук через мост Claude Code |
| [opencode](harnesses.ru.md#opencode) | Skill, в виде скопированного файла |
| [Devin CLI](harnesses.ru.md#devin-cli) | Skill и хук (hook), в виде плагина |
| [Factory Droid](harnesses.ru.md#factory-droid) | Skill и хук (hook), в виде плагина |
| [GitHub Copilot CLI](harnesses.ru.md#github-copilot-cli) | Skill и хук (hook), в виде плагина |
| [Antigravity, Gemini CLI, Kimi Code, Pi и Hermes Agent](harnesses.ru.md#everywhere-else-the-skill-on-its-own) | Skill, в виде скопированного файла |

---

Эта страница является переводом [install.md](install.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.
