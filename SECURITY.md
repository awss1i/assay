<h1 align="center">Security</h1>

---

<p align="center"><strong>Report a vulnerability privately, never in a public issue.</strong> Use
<a href="https://github.com/awss1i/assay/security/advisories/new">Report a vulnerability</a>
on the Security tab. A fix goes out as a new release on PyPI.</p>

---

## Contents

- [What Counts](#what-counts)
- [Supported Versions](#supported-versions)

---

## What Counts

assay opens pages nobody has reviewed, so these are its security boundaries:

- It serves the folder you point it at, over loopback only (`127.0.0.1`, on a
  random port), and nothing outside that folder.
- It opens the page in Chromium through Playwright.
- It never runs a build or installs anything.
- The plugin's hook runs `assay` on the pages a turn changed, and nothing else.

Getting around any of these is a vulnerability: the server answering on
anything but loopback or serving a file outside the folder, a page reaching
outside the browser through assay, the hook running anything other than
`assay`, or assay running a build.

Anything a page can normally do inside a browser is not a vulnerability.

---

## Supported Versions

The latest release on PyPI.
