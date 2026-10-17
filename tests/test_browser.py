"""Tests for what the local server hands the page under test, and how the
browser is launched. A page can send anything it reads to the internet, so
the server keeps to the folder's own files. None of these need Chromium.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

import pytest

from assay.browser import serve, servable


def write(root: Path, name: str, text: str = "x") -> Path:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text, encoding="utf-8")
    return root / name


def status(base: str, path: str) -> int:
    try:
        with urllib.request.urlopen(base + path, timeout=5) as answer:
            return answer.status
    except urllib.error.HTTPError as refused:
        return refused.code


@pytest.fixture
def site(tmp_path: Path) -> Path:
    root = tmp_path / "site"
    write(root, "index.html", "<!doctype html><body>hi")
    write(root, "app.js")
    write(root, "data/items.json", "[]")
    return root


def test_the_page_and_its_files_are_served(site: Path) -> None:
    with serve(site) as base:
        assert status(base, "/index.html") == 200
        assert status(base, "/app.js") == 200
        assert status(base, "/data/items.json") == 200


def test_hidden_files_and_folders_are_not_served(site: Path) -> None:
    write(site, ".env", "KEY=secret")
    write(site, ".git/config")
    write(site, "data/.token")

    with serve(site) as base:
        assert status(base, "/.env") == 404
        assert status(base, "/.git/config") == 404
        assert status(base, "/.git/") == 404
        assert status(base, "/data/.token") == 404


def test_a_symlink_out_of_the_folder_is_not_served(
        site: Path, tmp_path: Path) -> None:
    outside = write(tmp_path / "elsewhere", "secret.txt")
    (site / "secret.txt").symlink_to(outside)
    (site / "elsewhere").symlink_to(outside.parent, target_is_directory=True)

    with serve(site) as base:
        assert status(base, "/secret.txt") == 404
        assert status(base, "/elsewhere/secret.txt") == 404


def test_a_symlink_that_stays_in_the_folder_is_served(site: Path) -> None:
    (site / "alias.js").symlink_to(site / "app.js")

    with serve(site) as base:
        assert status(base, "/alias.js") == 200


def test_a_path_cannot_climb_out_of_the_folder(
        site: Path, tmp_path: Path) -> None:
    write(tmp_path, "secret.txt")

    with serve(site) as base:
        assert status(base, "/../secret.txt") != 200
        assert status(base, "/%2e%2e/secret.txt") != 200


def test_a_path_outside_the_folder_is_never_servable(tmp_path: Path) -> None:
    assert not servable(tmp_path / "site", tmp_path / "secret.txt")


class FakeChromium:
    """Records each launch, and refuses a sandboxed one when told to."""

    def __init__(self, sandbox_starts: bool) -> None:
        self.sandbox_starts = sandbox_starts
        self.launches: list = []

    def launch(self, **kw):
        from playwright.sync_api import Error

        self.launches.append(kw)
        if kw.get("chromium_sandbox") and not self.sandbox_starts:
            raise Error("No usable sandbox!")
        return self

    def close(self) -> None:
        pass


def launched(tmp_path: Path, monkeypatch, sandbox_starts: bool):
    """Open `run.Browser` against a stand-in for Playwright."""
    import playwright.sync_api

    from assay.run import Browser

    chromium = FakeChromium(sandbox_starts)

    class Play:
        def __init__(self) -> None:
            self.chromium = chromium

        def start(self):
            return self

        def stop(self) -> None:
            pass

    monkeypatch.setattr(playwright.sync_api, "sync_playwright", Play)
    with Browser(tmp_path, "index.html") as engine:
        return engine.sandboxed, chromium.launches


def test_the_browser_asks_for_the_sandbox(tmp_path: Path, monkeypatch) -> None:
    """Playwright turns the sandbox off unless asked."""
    sandboxed, launches = launched(tmp_path, monkeypatch, sandbox_starts=True)

    assert sandboxed is True
    assert [kw["chromium_sandbox"] for kw in launches] == [True]
    assert "--no-sandbox" not in launches[0]["args"]


def test_without_a_sandbox_the_page_still_runs_and_that_is_recorded(
        tmp_path: Path, monkeypatch) -> None:
    sandboxed, launches = launched(tmp_path, monkeypatch, sandbox_starts=False)

    assert sandboxed is False
    assert [kw["chromium_sandbox"] for kw in launches] == [True, False]
