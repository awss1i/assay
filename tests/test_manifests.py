"""Tests for the plugin and marketplace manifests each harness reads. A value a
harness doesn't accept can stop the whole marketplace from loading, and
nothing else in the suite would notice.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "assay"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_marketplace_points_at_the_plugin() -> None:
    for where in (".claude-plugin", ".cursor-plugin", ".grok-plugin",
                  ".github/plugin"):
        entry = read(ROOT / where / "marketplace.json")["plugins"][0]
        assert (ROOT / entry["source"]).resolve() == PLUGIN, where

    codex = read(ROOT / ".agents" / "plugins" / "marketplace.json")
    assert (ROOT / codex["plugins"][0]["source"]["path"]).resolve() == PLUGIN


def test_the_codex_policy_uses_values_codex_accepts() -> None:
    """Codex rejects the whole marketplace file over one unknown value."""
    policy = read(ROOT / ".agents" / "plugins" / "marketplace.json")[
        "plugins"][0]["policy"]

    assert policy["installation"] in {
        "NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
    assert policy["authentication"] in {"ON_INSTALL", "ON_USE"}


def test_cursor_gets_no_hook() -> None:
    """Cursor reads `hooks/hooks.json` unless the manifest names another
    file, and that file is in Claude Code's format, which Cursor doesn't
    document for plugins. Cursor gets the skill only."""
    manifest = read(PLUGIN / ".cursor-plugin" / "plugin.json")
    hooks = read(PLUGIN / manifest["hooks"])

    assert manifest["hooks"] != "./hooks/hooks.json"
    assert hooks["hooks"] == {}


def test_every_plugin_manifest_has_the_package_version() -> None:
    version = re.search(r'^version = "([^"]+)"',
                        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                        re.M).group(1)

    for where in (".claude-plugin", ".cursor-plugin", ".codex-plugin"):
        assert read(PLUGIN / where / "plugin.json")["version"] == version, where
