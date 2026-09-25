# Security

**Report a vulnerability privately, never in a public issue.** Use
[Report a vulnerability](https://github.com/awss1i/assay/security/advisories/new)
on the Security tab. A fix goes out as a new release on PyPI.

## What Counts

assay opens pages nobody has read, so the lines it draws around your machine
are the part that matters:

- It serves the folder you point it at, over loopback only (`127.0.0.1`, on a
  random port), and nothing outside that folder.
- It opens the page in Chromium through Playwright.
- It never runs a build or installs anything.
- The plugin's hook runs `assay` on the pages a turn changed, and nothing else.

A way around any of those is a vulnerability: the server answering off
loopback or handing out a file outside the folder, a page reaching past the
browser through assay, the hook running something other than `assay`, or
assay running a build.

A page doing what any page can do inside a browser is not.

## Supported Versions

The latest release on PyPI.
