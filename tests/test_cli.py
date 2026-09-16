"""What the command refuses to open, and what it says instead.

`unbuilt` is the one place assay draws a line around what it will do to your
machine, so the line is asserted rather than described.
"""

from __future__ import annotations

from pathlib import Path

from assay.cli import aimed, main, unbuilt


def write(root: Path, name: str, text: str = "") -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text, encoding="utf-8")


def test_a_plain_page_is_opened(tmp_path: Path) -> None:
    write(tmp_path, "index.html", "<!doctype html><body><h1>hi</h1>")
    assert unbuilt(tmp_path, "index.html") == ""


def test_a_page_loading_a_bundle_is_opened(tmp_path: Path) -> None:
    """Built output names a `.js` file, and that is the ordinary case."""
    write(tmp_path, "index.html",
          '<script type="module" src="/assets/index-C9t0.js"></script>')
    assert unbuilt(tmp_path, "index.html") == ""


def test_a_source_tree_is_refused_with_the_command_to_run(
        tmp_path: Path) -> None:
    """A Vite root page names a module no browser can execute.

    Served as it stands the page renders nothing, which assay would report
    as a program that renders nothing, a true statement about the folder
    and a false one about the program.
    """
    write(tmp_path, "index.html",
          '<div id="root"></div>'
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "src/main.jsx", "export default 1")
    write(tmp_path, "package.json", "{}")

    why = unbuilt(tmp_path, "index.html")
    assert "npm run build" in why
    assert "will not run that for you" in why


def test_the_source_file_being_present_decides_nothing(
        tmp_path: Path) -> None:
    """The first version of this treated a missing file as the signal.

    Backwards: a source tree is exactly where `src/main.jsx` *does* exist,
    so the check passed on the case it was written for. A browser cannot run
    JSX whether the file is there or not, because the extension is the whole test.
    """
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "package.json", "{}")
    assert "npm run build" in unbuilt(tmp_path, "index.html")

    write(tmp_path, "src/main.jsx", "export default 1")
    assert "npm run build" in unbuilt(tmp_path, "index.html")


def test_an_already_built_folder_is_pointed_at(tmp_path: Path) -> None:
    """Having done the build, the useful answer is where it went."""
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "package.json", "{}")
    write(tmp_path, "dist/index.html", "<body><h1>built</h1>")

    why = unbuilt(tmp_path, "index.html")
    assert "dist" in why and "npm install" not in why


def test_a_missing_page_with_no_project_says_only_that(
        tmp_path: Path) -> None:
    """No package.json means no build to suggest, so none is suggested."""
    assert unbuilt(tmp_path, "index.html").endswith("does not exist")


def test_if_page_says_nothing_about_a_folder_that_is_not_a_page(
        tmp_path: Path, capsys) -> None:
    """A hook fires on every write and most writes are not a page.

    Without this it answers a Rust file, a README and every component in a
    source tree with a paragraph about building first, and that paragraph
    lands in somebody's conversation. Nothing, and exit 0.
    """
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "src/main.jsx", "export default 1")
    write(tmp_path, "package.json", "{}")

    code = main([str(tmp_path), "--if-page"])
    said = capsys.readouterr()

    assert code == 0
    assert said.out == "" and said.err == ""


def test_without_if_page_the_same_folder_is_still_refused_out_loud(
        tmp_path: Path, capsys) -> None:
    """The twin. Silence is for the caller that did not ask.

    Somebody who typed `assay .` at a source tree is owed the reason and the
    command to run, and quietly exiting 0 on them would be the worst of both:
    no check, and no sign that none happened.
    """
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "src/main.jsx", "export default 1")
    write(tmp_path, "package.json", "{}")

    code = main([str(tmp_path)])
    said = capsys.readouterr()

    assert code == 2
    assert "source tree" in said.err
    assert "npm run build" in said.err


def test_a_page_is_split_into_the_folder_and_the_page(tmp_path: Path) -> None:
    """`assay ./todo.html` is what somebody types at a one-file program.

    It used to answer *"todo.html/index.html does not exist"*: a folder named
    after the page, and a page nobody asked for. Measured on a live harness
    run, where a model handed a single-file program typed exactly that.
    """
    write(tmp_path, "todo.html", "<!doctype html><body><h1>hi</h1>")

    assert aimed(str(tmp_path / "todo.html"), "index.html") == (
        tmp_path, "todo.html")


def test_a_page_that_was_never_written_is_still_a_page(
        tmp_path: Path) -> None:
    """The suffix decides it, not whether anybody wrote the file.

    Otherwise the one case where the answer matters most, a page that is
    missing, is the one case the split does not happen for, and the message
    names a folder that was never meant.
    """
    assert aimed(str(tmp_path / "nope.html"), "index.html") == (
        tmp_path, "nope.html")


def test_a_folder_is_never_split(tmp_path: Path) -> None:
    """Including one whose own name ends in `.html`, which is legal."""
    (tmp_path / "site.html").mkdir()
    write(tmp_path, "site.html/index.html", "<!doctype html><body>hi")

    assert aimed(str(tmp_path / "site.html"), "index.html") == (
        tmp_path / "site.html", "index.html")


def test_a_missing_page_is_named_rather_than_a_folder_under_it(
        tmp_path: Path, capsys) -> None:
    """The whole point of the split, end to end."""
    code = main([str(tmp_path / "nope.html")])
    said = capsys.readouterr()

    assert code == 2
    assert said.err.strip().endswith("nope.html does not exist")
    assert "nope.html/index.html" not in said.err
