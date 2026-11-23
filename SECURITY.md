<h1 align="center">Security</h1>

<p align="center"><a href="README.md">assay</a> › Security</p>

<p align="center">How to report a vulnerability in assay, and what counts as one.</p>

---

## Contents

- [Reporting a vulnerability](#reporting-a-vulnerability)
- [What counts](#what-counts)
- [Supported versions](#supported-versions)

---

## Reporting a vulnerability

Report a vulnerability privately, never in a public issue. Use Report a
vulnerability on the repository's Security tab. A fix goes out as a new
release on PyPI.

[Report a vulnerability](https://github.com/awss1i/assay/security/advisories/new)

---

## What counts

assay opens pages nobody has reviewed, so these are its security boundaries:

- It serves the folder you point it at, over loopback only (`127.0.0.1`, on a
  random port). It serves nothing outside that folder, no hidden file or
  folder such as `.env` or `.git/`, and no symlink that leads out of the
  folder.
- It opens the page in Chromium through Playwright, with Chromium's sandbox
  on. Where the sandbox can't start, such as when running as root or in some
  containers, it runs the page without the sandbox and prints a warning.
- It never runs a project's build or installs its dependencies. The only
  thing it downloads is Chromium, through Playwright, on the first run.
- The plugin's hook runs `assay` on the pages a turn changed, and nothing else.

Getting around any of these is a vulnerability: the server answering on
anything but loopback or serving a file it shouldn't, a page reaching
outside the browser through assay, the hook running anything other than
`assay`, or assay running a build.

Anything a page can normally do inside a browser is not a vulnerability. That
includes reaching the internet, so a page can send out any file the server
gives it. Keep secrets out of the folder you check, or in hidden files.

---

## Supported versions

The latest release on PyPI.
