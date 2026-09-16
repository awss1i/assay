# The Skill and the Plugin

Two ways to have your agent check a page it just wrote. The skill is one
markdown file and works anywhere; the plugin is that skill plus a hook, so
the check happens without the agent deciding to run it.

**[How to install either, for fifteen harnesses →](../../docs/harnesses.md)**

## Contents

- [The Skill](#the-skill)
- [The Plugin](#the-plugin)
- [What Both Refuse to Do](#what-both-refuse-to-do)

## The Skill

*All fifteen harnesses.*

[`skills/checking-a-page/SKILL.md`](skills/checking-a-page/SKILL.md) tells the
agent to run one command when it has finished a page:

```bash
assay <the page> --one-line
```

and to print what comes back as the last thing in its reply:

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

or, when something is wrong:

```
assay: checked notes/index.html, 12 checks, 2 flagged:
  - press Clear all: the page threw and stopped running: Cannot set properties of null (setting 'innerHTML')
  - press Add, then Clear all: the page threw and stopped running: Cannot set properties of null (setting 'innerHTML')
```

The sentence is assay's own. `--one-line` prints it, and the agent repeats it
rather than composing one, so the numbers and the wording cannot drift from
what was measured.

The agent decides when to run it. That is the whole difference from the
plugin.

## The Plugin

*Claude Code and the DeepSeek Harness.*

The same skill plus a `Stop` hook, so the check runs at the end of every turn
that touched a page whether or not the agent thought to do it.

**It finds pages by looking at the disk.** Any web file changing marks the
page it sits with, so editing `app.js` counts even though no HTML moved.
Within a folder it checks the most recently written `.html`, with
`index.html` winning a tie, because the name is the agent's to choose and a
page is often called `todo.html`.

**It is bounded three ways** so a turn stays cheap: four folders deep with
`node_modules` and `.git` skipped, a time window so a page nobody touched is
left alone, and at most three pages a turn.

**It speaks every time it checks something**, clean or not. A hook that says
nothing when the page is fine says the same nothing when assay is missing,
when it crashed, and when it never fired. A turn that touched no page says
nothing, because there is nothing to report.

**It holds the turn open** so the line reaches a person rather than being
filed where the conversation has already ended. Two things stop it doing that
twice: the harness's own `stop_hook_active` flag, and a clock it writes when
it scans. The clock goes in the harness's scratch folder when it offers one,
otherwise in `.git/` when the working directory is a repository, and
otherwise in one `.assay-last-run` file in the working directory. With
nowhere to write the clock it reports once and does not hold the turn.

## What Both Refuse to Do

**They report and never fix.** assay has not been told what the page is for.
It presses what the page offers and reports what followed, so a finding is a
place to look rather than a confirmed defect: a control can legitimately do
nothing in the state it was pressed in, and a value can be clamped on
purpose.

Changing working code because of an unchecked finding is the expensive
mistake, so the agent hands over what it pressed and what happened and leaves
the judgement with you. Ask it to fix something and it will.
