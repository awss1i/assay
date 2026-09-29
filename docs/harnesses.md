# Installing assay in Your Harness

Install steps for fifteen harnesses. Six install assay with their own plugin
command. For the other nine, you copy the skill file into place, which works
in any harness that reads skills.

## Contents

- [What You Get](#what-you-get)
- [Claude Code](#claude-code)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [Everywhere Else: The Skill on Its Own](#everywhere-else-the-skill-on-its-own)

## What You Get

assay comes in two parts:

- a **skill**, which tells your agent to run `assay` after it finishes a page
  and show you the result, and
- a **hook**, which runs the check automatically.

A plugin install gives you both. The hook works in Claude Code and the
DeepSeek Harness, where the check runs at the end of every turn that changed a
page. In the other harnesses the agent runs the check itself, as the skill
tells it to. opencode and the harnesses under
[Everywhere Else](#everywhere-else-the-skill-on-its-own) install the skill
only, and the DeepSeek Harness uses the hook only, through its Claude Code
bridge.

All fifteen need `assay` on your `PATH` first:

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # no Python 3.10+? uv downloads one
```

```bash
pipx install assay-ui          # its own environment, for when pip says "externally managed"
```

## Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

## DeepSeek Harness

dsh runs Claude Code hook configs through a bridge that ships with it. No
profile carries the bridge, so add it in `$DSH_HOME/cordis.patch.yml`, which
is applied after every profile's own layer and so covers `web`, `headless`
and any profile you make:

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

## opencode

```bash
mkdir -p .claude/skills
cp -r plugins/assay/skills/checking-a-page .claude/skills/
```

opencode reads `.claude/skills/`, `.opencode/skills/`, `.agents/skills/` and
`~/.config/opencode/skills/`. Prefer `.claude/skills/`: Claude Code reads it
too, so one folder serves both.

## Devin CLI

```bash
devin plugins install awss1i/assay#plugins/assay
```

The plugin lives in `plugins/assay`, and `#` is how Devin is told to look
there. Update with `devin plugins update assay`.

## Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

## GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

## Everywhere Else: The Skill on Its Own

*Antigravity, Codex App, Codex CLI, Cursor, Gemini CLI, Grok Build CLI, Kimi
Code, Pi, Hermes Agent.*

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
