# Installing assay in Your Harness

Install steps for fifteen harnesses. Six take assay through their own install
command. The other nine take the skill as a file, which works anywhere that
reads skills.

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

assay comes in two parts: a **skill**, which tells your agent to run `assay`
when it finishes a page and print what came back, and a **hook**, which does
it without being asked. The plugin installs are the two together.

The hook runs in Claude Code and the DeepSeek Harness, so there the check
happens at the end of every turn that touched a page. Everywhere else, count
on the skill: the agent runs the check itself. opencode and the harnesses under
[Everywhere Else](#everywhere-else-the-skill-on-its-own) take the skill alone,
and the DeepSeek Harness takes the hook alone, through its Claude Code bridge.

All fifteen need `assay` on your `PATH` first. It needs Python 3.10 or newer:

```bash
pip install assay-ui        # or: uv tool install assay-ui, pipx install assay-ui
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

Each of these packages plugins its own way, and assay does not ship a plugin
in their formats, so the skill goes in as a file. It is one markdown file and
works anywhere that reads skills or instruction files.

Copy
[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page)
into the folder your harness reads skills from, for example a project's
`.agents/skills/`, which Hermes Agent reads, or paste the file into your
`AGENTS.md`.

What you lose is the hook: the agent decides when to run the check rather
than it happening at the end of every turn.

**[How the skill behaves →](../plugins/assay/README.md#the-skill)**
