"""Check that each translation is up to date with its English source.

A translation's first line records the git blob id of its English source, so
when the English changes, the ids stop matching and the test names the stale
translation. docs/i18n/rules.md describes the convention.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("zh-CN", "ja", "ko", "ru")
STAMP = re.compile(r"<!-- i18n-source: (\S+) ([0-9a-f]{40}) -->")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^#{2,6}\s+(.*?)\s*$")
ANCHOR = re.compile(r'<a id="([^"]+)"></a>')


def blob_id(path: Path) -> str:
    """The id git gives the file's contents, the same as `git hash-object`."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def find_translations() -> list[Path]:
    found = []
    for path in ROOT.rglob("*.md"):
        parts = path.relative_to(ROOT).parts
        if any(p.startswith(".") or p in ("node_modules", "__pycache__") for p in parts):
            continue
        if any(path.name.endswith(f".{lang}.md") for lang in LANGS):
            found.append(path)
    return sorted(found)


def source_of(translation: Path) -> Path:
    for lang in LANGS:
        suffix = f".{lang}.md"
        if translation.name.endswith(suffix):
            return translation.with_name(translation.name[: -len(suffix)] + ".md")
    raise ValueError(translation)


def headings(path: Path) -> list[str]:
    """Heading text below the title, skipping lines inside code blocks."""
    found, in_code = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_code = not in_code
        elif not in_code and (m := HEADING.match(line)):
            found.append(m.group(1))
    return found


def github_ids(texts: list[str]) -> list[str]:
    """The ids GitHub gives these English headings, numbering repeats."""
    ids, seen = [], {}
    for text in texts:
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).replace("`", "").replace("*", "")
        base = re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")
        n = seen.get(base, 0)
        seen[base] = n + 1
        ids.append(base if n == 0 else f"{base}-{n}")
    return ids


TRANSLATIONS = find_translations()


def test_translations_exist():
    assert TRANSLATIONS, "no translated docs found"


def test_each_translated_doc_has_every_language():
    missing = []
    for source in sorted({source_of(t) for t in TRANSLATIONS}):
        for lang in LANGS:
            expected = source.with_name(source.name[:-3] + f".{lang}.md")
            if not expected.exists():
                missing.append(rel(expected))
    assert not missing, f"missing translations: {', '.join(missing)}"


@pytest.mark.parametrize("translation", TRANSLATIONS, ids=rel)
def test_translation_matches_the_current_english(translation):
    source = source_of(translation)
    first = translation.read_text(encoding="utf-8").splitlines()[0]
    m = STAMP.fullmatch(first)
    assert m, f"{rel(translation)} has no i18n-source line, run docs/i18n/stamp.py on it"
    assert m.group(1) == rel(source), f"{rel(translation)} names the wrong source"
    assert m.group(2) == blob_id(source), (
        f"{rel(source)} changed after {rel(translation)} was translated. "
        f"See what changed with `git diff {m.group(2)} HEAD:{rel(source)}`, update the "
        f"translation, then run `python docs/i18n/stamp.py {rel(translation)}`. "
        f"docs/i18n/rules.md has the details.")


@pytest.mark.parametrize("translation", TRANSLATIONS, ids=rel)
def test_translation_has_the_same_headings(translation):
    english = github_ids(headings(source_of(translation)))
    anchors = []
    for text in headings(translation):
        m = ANCHOR.match(text)
        assert m, f"a heading in {rel(translation)} has no anchor: {text}"
        anchors.append(m.group(1))
    assert anchors == english
