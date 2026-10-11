<!-- i18n-source: docs/harnesses.md 35ce1703961c0b049eb853466b5b884081a86ff7 -->

<h1 align="center">Установка assay в ваш harness</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <a href="harnesses.ja.md">日本語</a> · <a href="harnesses.ko.md">한국어</a> · <b>Русский</b></p>

---

<p align="center">Шаги установки для пятнадцати harness (среда запуска агента). Шесть из них
устанавливают assay собственной командой для плагинов. Для остальных девяти вы копируете файл
skill в нужное место, и этот способ работает в любом harness, который читает файлы skill.</p>

---

## <a id="contents"></a>Содержание

- [Что вы получаете](#what-you-get)
- [Claude Code](#claude-code)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [Только skill для остальных harness](#everywhere-else-the-skill-on-its-own)

---

## <a id="what-you-get"></a>Что вы получаете

assay состоит из двух частей:

- **skill**, который говорит агенту запускать `assay` после того, как он закончил страницу, и
  показывать вам результат,
- **хук (hook)**, который запускает проверку (check) автоматически.

Установка плагина (plugin) даёт вам обе части. Хук работает в Claude Code и DeepSeek Harness,
где проверка запускается в конце каждого хода (turn), в котором изменилась страница. В остальных
harness агент запускает проверку сам, как велит ему skill. opencode и
[остальные harness](#everywhere-else-the-skill-on-its-own) устанавливают только skill, а DeepSeek
Harness использует только хук через свой мост для Claude Code.

Всем пятнадцати сначала нужен `assay` в вашем `PATH`.

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # нет Python 3.10+? uv скачает его сам
```

```bash
pipx install assay-ui          # устанавливает assay в отдельное изолированное окружение
```

---

## <a id="claude-code"></a>Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh выполняет конфигурации хуков Claude Code через мост, который входит в его поставку. Ни один
профиль не подключает этот мост, поэтому добавьте его в `$DSH_HOME/cordis.patch.yml`. Этот файл
применяется после собственного слоя каждого профиля, поэтому он действует на `web`, `headless`
и любой профиль, который вы создадите.

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: /abs/path/to/assay/plugins/assay/hooks/hooks.json
        pluginRoot: /abs/path/to/assay/plugins/assay
```

Если вы не задали `$DSH_HOME`, он равен `~/.dsh`. Оба пути абсолютные, потому что хук
запускается в собственной рабочей директории. `dsh --dump-config` выводит итоговое дерево
конфигурации, и именно по нему видно, что мост подключился.

Чтобы мост действовал только в одном профиле, поместите тот же блок в `cordis.patch.yml` этого
профиля или передавайте его при каждом запуске через `--patch`.

---

## <a id="opencode"></a>opencode

```bash
mkdir -p .claude/skills
cp -r plugins/assay/skills/checking-a-page .claude/skills/
```

opencode читает `.claude/skills/`, `.opencode/skills/`, `.agents/skills/` и
`~/.config/opencode/skills/`. Лучше используйте `.claude/skills/`. Эту папку читает и Claude
Code, так что одна папка подходит обоим.

---

## <a id="devin-cli"></a>Devin CLI

```bash
devin plugins install awss1i/assay#plugins/assay
```

Плагин находится в `plugins/assay`, а символ `#` указывает Devin искать его там. Обновляйте его
командой `devin plugins update assay`.

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

---

## <a id="everywhere-else-the-skill-on-its-own"></a>Только skill для остальных harness

*Antigravity, Codex App, Codex CLI, Cursor, Gemini CLI, Grok Build CLI, Kimi
Code, Pi, Hermes Agent.*

assay не поставляет плагин в форматах этих harness, поэтому вы устанавливаете skill как файл. Это
один файл в формате Markdown, и он работает везде, где читаются файлы skill или файлы с
инструкциями.

Скопируйте
[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page)
в папку, из которой ваш harness читает файлы skill, например в `.agents/skills/` проекта, которую
читает Hermes Agent. Или вставьте содержимое файла в ваш `AGENTS.md`.

Без хука агент сам решает, когда запускать проверку, и она не запускается автоматически в конце
каждого хода.

**[Как работает skill →](../plugins/assay/README.ru.md#the-skill)**

---

Эта страница является переводом [harnesses.md](harnesses.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.
