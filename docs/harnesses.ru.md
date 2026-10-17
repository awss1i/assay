<!-- i18n-source: docs/harnesses.md 754a27f7ad6e3db62fad6db5ec61f13ed63618f1 -->

<h1 align="center">Установка assay в ваш harness</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <a href="harnesses.ja.md">日本語</a> · <a href="harnesses.ko.md">한국어</a> · <b>Русский</b></p>

---

<p align="center">Шаги установки для пятнадцати harness (среда запуска агента). Восемь из них
устанавливают assay собственной командой для плагинов. Для остальных семи вы копируете файл
skill в нужное место, и этот способ работает в любом harness, который читает файлы skill.</p>

---

## <a id="contents"></a>Содержание

- [Что вы получаете](#what-you-get)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Grok Build CLI](#grok-build-cli)
- [Cursor](#cursor)
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

Установка плагина (plugin) даёт вам обе части, за исключением Cursor, где она даёт только skill.
В Claude Code, Codex, Grok Build CLI, Devin CLI, Factory Droid, GitHub Copilot CLI и DeepSeek
Harness хук запускает проверку в конце каждого хода (turn), в котором изменилась страница.
DeepSeek Harness получает skill в виде скопированного файла, а хук подключает через свой мост для
Claude Code. opencode и [остальные harness](#everywhere-else-the-skill-on-its-own) получают
только skill, и в них агент запускает проверку сам, как велит ему skill.

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

## <a id="codex"></a>Codex

В Codex CLI добавьте маркетплейс и установите плагин.

```bash
codex plugin marketplace add awss1i/assay
codex plugin add assay@assay
```

Затем начните новую сессию, откройте `/hooks` и отметьте хук assay как доверенный. Пока вы не
отметите хук плагина как доверенный, Codex его пропускает, поэтому без этого шага вы получите
только skill. Обновляйте плагин командой `codex plugin marketplace upgrade assay`.

В Codex App, то есть в Codex внутри десктопного приложения ChatGPT, выполните приведённую выше
команду `codex plugin marketplace add`, перезапустите приложение и установите assay из
маркетплейса assay в разделе «Plugins».

---

## <a id="grok-build-cli"></a>Grok Build CLI

```bash
grok plugin marketplace add awss1i/assay
grok plugin install assay --trust
```

Без `--trust` Grok не устанавливает плагин, в котором есть хук. Он останавливается и просит вас
выполнить команду ещё раз с `--trust`. Если установка прошла успешно, `grok inspect` покажет
skill `checking-a-page` и хук. Для обновления выполните `grok plugin marketplace update`, а затем
`grok plugin update assay`.

---

## <a id="cursor"></a>Cursor

В редакторе, начиная с Cursor 2.5, введите эту команду в чате Agent.

```
/add-plugin assay@https://github.com/awss1i/assay
```

В Cursor CLI добавьте маркетплейс, а затем установите assay через `/plugin` в сессии.

```bash
agent plugin marketplace add https://github.com/awss1i/assay
```

В обоих случаях вы получаете skill. В Cursor плагин не добавляет хук, потому что хуки Cursor
используют другой формат. Чтобы вместо этого установить только skill, воспользуйтесь CLI skills.

```bash
npx skills add awss1i/assay --agent cursor       # для этого проекта, в .agents/skills/
npx skills add awss1i/assay --agent cursor -g    # для всех проектов, в ~/.agents/skills/
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh читает файлы skill из `.agents/skills/` в вашем проекте и из `~/.agents/skills/` для всех
проектов, но не из `.claude/skills/`. Скопируйте skill в одну из этих папок.

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

В режиме разрешений по умолчанию dsh не даёт команде записывать файлы за пределами вашего
проекта, а первая проверка скачивает Chromium в вашу домашнюю папку, поэтому dsh может один раз
попросить вас это разрешить. Чтобы обойтись без такого запроса, запустите первую проверку из
своей командной оболочки.

Для хука dsh использует мост, который входит в его поставку и выполняет конфигурации хуков
Claude Code. Ни один профиль не подключает этот мост, поэтому добавьте его в
`$DSH_HOME/cordis.patch.yml`. Этот файл
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
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

opencode читает `.agents/skills/`, `.opencode/skills/`, `.claude/skills/` и
`~/.config/opencode/skills/`. Лучше используйте `.agents/skills/`. Эту папку читают также
DeepSeek Harness, Cursor и Hermes Agent, так что одна папка подходит всем четырём.

---

## <a id="devin-cli"></a>Devin CLI

Devin управляет плагинами, только когда вы вошли в аккаунт, поэтому сначала выполните
`devin auth login`.

```bash
devin plugins install awss1i/assay#plugins/assay
```

Плагин находится в `plugins/assay`, а символ `#` указывает Devin искать его там. Добавьте
`--local`, чтобы установить плагин только на этот компьютер, а не в ваш манифест Devin Cloud.
Обновляйте его командой `devin plugins update assay`. Devin старается запускать хуки плагинов, но
не гарантирует этого, а хук, который завершился с ошибкой, не останавливает ход.

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

В интерактивном режиме Droid хуки запускаются только в папке, которую вы отметили как доверенную.

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

Copilot показывает результат хука прямо вам, а не передаёт его агенту. Вы видите его в своём
терминале под строкой, предназначенной для агента, и агент его не повторяет.

---

## <a id="everywhere-else-the-skill-on-its-own"></a>Только skill для остальных harness

*Antigravity, Gemini CLI, Kimi Code, Pi, Hermes Agent.*

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
