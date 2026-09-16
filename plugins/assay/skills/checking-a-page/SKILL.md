---
name: checking-a-page
description: Check that a web page you wrote or changed actually works, by opening it in a browser and driving every control on it. Use after creating or editing an HTML page, or the JavaScript or CSS that a page loads.
---

# Checking a page

A page you have just written has no tests, no baseline and no history, so the
usual ways of asking whether it works all need something that does not exist
yet. `assay` opens the page in a real browser, works out what it offers,
drives all of it, and reports what it did and what happened.

## When to run it

**When the work is done**, not while you are still making changes. Run it once
at the end, after the last edit, on each page you touched.

That includes editing the JavaScript or CSS a page loads, not only the HTML
itself, and the page is often a folder or two above the file you changed.

## Run exactly this

```bash
assay <the page you changed> --one-line
```

Point it at the page itself, `todo.html` or `dist/index.html`. A folder works
too and opens `index.html` inside it. No key, no network, no configuration. A
small page takes seconds, a busy one up to a minute or more.

## Then print what it printed

Put its output, **verbatim**, as the last thing in your reply. It is already
one line, or one line and a short list, and it is already worded. Do not
summarise it, reformat it, add to it, or write it yourself.

It looks like this, and the numbers and wording are assay's own:

```
assay: checked <page>, <n> checks, nothing flagged.
```

Print it whether it flagged anything or not. A reader who is told nothing
cannot tell a clean page from a check that never ran, and both look like
silence.

**If the command did not run, say so instead, in your own words**, naming the
page and quoting what the shell actually said. Never describe a check that did
not happen as one that passed, and never state a cause you did not see: if the
shell said something, that is the cause, and if you did not read it, say only
that it did not run.

## Do not act on what it found

**Report it and stop.** Do not edit code in response to a finding in the same
reply.

assay has not been told what the page is for. It presses what the page offers
and reports what followed, so a finding is a place to look and not a confirmed
defect: a control can legitimately do nothing in the state it was pressed in,
and a value can be clamped on purpose. Changing working code because of a
finding nobody has checked is the one outcome worth avoiding, and it is why
this reports rather than fixes.

If the person you are working with asks you to fix it, then fix it.

## What it will not do

- **It will not build your project.** Point it at built output. Given a source
  tree it says so and names the command, and it will not run `npm install` for
  you, because installing dependencies executes their setup scripts.
- **It checks one page.** It does not crawl. A site means running it per page.
- **It cannot know intent.** A control that works mechanically and does the
  wrong thing is not something it can see.
