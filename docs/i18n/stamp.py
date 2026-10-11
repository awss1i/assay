"""Record which version of its English source a translation was made from.

    python docs/i18n/stamp.py README.zh-CN.md docs/usage.ja.md

Run it after updating a translation. It writes the English source's git blob id
into the translation's first line, the line tests/test_translations.py checks.
docs/i18n/rules.md describes the whole convention.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("zh-CN", "ja", "ko", "ru")


def blob_id(path: Path) -> str:
    """The id git gives the file's contents, the same as `git hash-object`."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def source_of(translation: Path) -> Path:
    for lang in LANGS:
        suffix = f".{lang}.md"
        if translation.name.endswith(suffix):
            return translation.with_name(translation.name[: -len(suffix)] + ".md")
    sys.exit(f"{translation} isn't named like a translation, name.<{'|'.join(LANGS)}>.md")


def stamp(translation: Path) -> None:
    source = source_of(translation)
    rel = source.relative_to(ROOT).as_posix()
    line = f"<!-- i18n-source: {rel} {blob_id(source)} -->\n"
    lines = translation.read_text(encoding="utf-8").splitlines(keepends=True)
    if lines and lines[0].startswith("<!-- i18n-source:"):
        lines[0] = line
    else:
        lines[:0] = [line, "\n"]
    translation.write_text("".join(lines), encoding="utf-8")
    print(f"stamped {translation.relative_to(ROOT).as_posix()} from {rel}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        stamp(Path(arg).resolve())
