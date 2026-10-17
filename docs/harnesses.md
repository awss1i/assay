<h1 align="center">Installing assay in Your Harness</h1>

<p align="center"><b>English</b> · <a href="harnesses.zh-CN.md">简体中文</a> · <a href="harnesses.ja.md">日本語</a> · <a href="harnesses.ko.md">한국어</a> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">Install steps for fifteen harnesses. Eight install assay with their own plugin
command. For the other seven, you copy the skill file into place, which works
in any harness that reads skills.</p>

---

## Contents

- [What You Get](#what-you-get)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Grok Build CLI](#grok-build-cli)
- [Cursor](#cursor)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [Everywhere Else: The Skill on Its Own](#everywhere-else-the-skill-on-its-own)

---

## What You Get

assay comes in two parts:

- a **skill**, which tells your agent to run `assay` after it finishes a page
  and show you the result, and
- a **hook**, which runs the check automatically.

A plugin install gives you both, except in Cursor, where it gives you the
skill alone. In Claude Code, Codex, Grok Build CLI, Devin CLI, Factory Droid,
GitHub Copilot CLI and the DeepSeek Harness, the hook runs the check at the end
of every turn that changed a page. The DeepSeek Harness gets the skill as a
copied file and the hook through its Claude Code bridge. opencode and the
harnesses under [Everywhere Else](#everywhere-else-the-skill-on-its-own) get
the skill alone, and there the agent runs the check itself, as the skill
tells it to.

All fifteen need `assay` on your `PATH` first:

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # no Python 3.10+? uv downloads one
```

```bash
pipx install assay-ui          # installs assay in its own isolated environment
```

---

## Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

---

## Codex

In Codex CLI, add the marketplace and install the plugin.

```bash
codex plugin marketplace add awss1i/assay
codex plugin add assay@assay
```

Then start a new session, open `/hooks` and trust the assay hook. Codex
skips a plugin's hook until you trust it, so without this step you get the
skill alone. Update with `codex plugin marketplace upgrade assay`.

In the Codex App, which is Codex in the ChatGPT desktop app, run the
`codex plugin marketplace add` command above, restart the app, and install
assay from the assay marketplace under Plugins.

---

## Grok Build CLI

```bash
grok plugin marketplace add awss1i/assay
grok plugin install assay --trust
```

Without `--trust`, Grok won't install a plugin that has a hook. It stops and
asks you to run the command again with `--trust`. `grok inspect` lists the
`checking-a-page` skill and the hook once the install has worked. Update with
`grok plugin marketplace update`, then `grok plugin update assay`.

---

## Cursor

In the editor, from Cursor 2.5, type this in an Agent chat.

```
/add-plugin assay@https://github.com/awss1i/assay
```

In the Cursor CLI, add the marketplace, then install assay from `/plugin` in
a session.

```bash
agent plugin marketplace add https://github.com/awss1i/assay
```

Either way you get the skill. The plugin doesn't add the hook in Cursor,
because Cursor's hooks take a different format. To install the skill on its
own instead, use the skills CLI.

```bash
npx skills add awss1i/assay --agent cursor       # this project, in .agents/skills/
npx skills add awss1i/assay --agent cursor -g    # every project, in ~/.agents/skills/
```

---

## DeepSeek Harness

dsh reads skills from `.agents/skills/` in your project and `~/.agents/skills/`
for every project, but not from `.claude/skills/`. Copy the skill into one of
them.

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

dsh's default permission mode stops a command writing outside your project,
and the first check downloads Chromium into your home folder, so dsh may ask
you to approve that once. To avoid the prompt, run your first check from
your own shell.

For the hook, dsh runs Claude Code hook configs through a bridge that ships
with it. No profile carries the bridge, so add it in
`$DSH_HOME/cordis.patch.yml`, which is applied after every profile's own layer
and so covers `web`, `headless` and any profile you make:

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: /abs/path/to/assay/plugins/assay/hooks/hooks.json
        pluginRoot: /abs/path/to/assay/plugins/assay
```

`$DSH_HOME` is `~/.dsh` unless you set it. Both paths are absolute, because
the hook runs with its own working directory. `dsh --dump-config` prints the
composed tree, so it is what tells you the bridge mounted.

To scope it to one profile, put the same block in that profile's
`cordis.patch.yml` instead, or pass it per run with `--patch`.

---

## opencode

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

opencode reads `.agents/skills/`, `.opencode/skills/`, `.claude/skills/` and
`~/.config/opencode/skills/`. Prefer `.agents/skills/`, because the DeepSeek
Harness, Cursor and Hermes Agent read it too, so one folder serves all four.

---

## Devin CLI

Devin manages plugins only when you're signed in, so run `devin auth login`
first.

```bash
devin plugins install awss1i/assay#plugins/assay
```

The plugin lives in `plugins/assay`, and `#` is how Devin is told to look
there. Add `--local` to install it on this machine only, instead of in your
Devin Cloud manifest. Update with `devin plugins update assay`. Devin runs
plugin hooks on a best-effort basis, and a hook that fails doesn't stop the
turn.

---

## Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

In the interactive Droid, hooks run only in a folder you've trusted.

---

## GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

Copilot shows the hook's report to you directly instead of passing it to the
agent. You see it in your terminal, under the line meant for the agent, and
the agent doesn't repeat it.

---

## Everywhere Else: The Skill on Its Own

*Antigravity, Gemini CLI, Kimi Code, Pi, Hermes Agent.*

assay doesn't ship a plugin in these harnesses' formats, so you install the
skill as a file. It's one markdown file and works anywhere that reads skills
or instruction files.

Copy
[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page)
into the folder your harness reads skills from, for example a project's
`.agents/skills/`, which Hermes Agent reads, or paste the file into your
`AGENTS.md`.

Without the hook, the agent decides when to run the check, instead of it
running at the end of every turn.

**[How the skill works →](../plugins/assay/README.md#the-skill)**
