"""Tests for how the command picks the folder and page to open, and what it
prints when it won't open them. assay never runs a project's build, so these
tests pin the message it prints instead.
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
    """A page that loads a built `.js` bundle is opened as it is."""
    write(tmp_path, "index.html",
          '<script type="module" src="/assets/index-C9t0.js"></script>')
    assert unbuilt(tmp_path, "index.html") == ""


def test_a_source_tree_is_refused_with_the_command_to_run(
        tmp_path: Path) -> None:
    """A Vite root page that loads `/src/main.jsx` is refused with the build
    command. A browser can't run JSX, so the page would render nothing and
    assay would wrongly report the program as blank.
    """
    write(tmp_path, "index.html",
          '<div id="root"></div>'
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "src/main.jsx", "export default 1")
    write(tmp_path, "package.json", "{}")

    why = unbuilt(tmp_path, "index.html")
    assert "npm run build" in why
    assert "won't run the build itself" in why


def test_the_source_file_being_present_decides_nothing(
        tmp_path: Path) -> None:
    """A `.jsx` entry is refused whether or not the file exists. A browser
    can't run JSX either way, and a source tree is where the file does exist.
    """
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "package.json", "{}")
    assert "npm run build" in unbuilt(tmp_path, "index.html")

    write(tmp_path, "src/main.jsx", "export default 1")
    assert "npm run build" in unbuilt(tmp_path, "index.html")


def test_an_already_built_folder_is_pointed_at(tmp_path: Path) -> None:
    """When `dist/index.html` exists, the message points at it instead of
    suggesting a build."""
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "package.json", "{}")
    write(tmp_path, "dist/index.html", "<body><h1>built</h1>")

    why = unbuilt(tmp_path, "index.html")
    assert "dist" in why and "npm install" not in why


def test_a_missing_page_with_no_project_says_only_that(
        tmp_path: Path) -> None:
    """Without a package.json there's no build to suggest, so the message only
    says the page doesn't exist."""
    assert unbuilt(tmp_path, "index.html").endswith("doesn't exist")


def test_if_page_says_nothing_about_a_folder_that_is_not_a_page(
        tmp_path: Path, capsys) -> None:
    """`--if-page` prints nothing and exits 0 on a folder it can't check.
    Editor hooks run it after every write, and most writes aren't a page, so
    any message here would land in the agent's conversation each time.
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
    """Without `--if-page`, the same folder exits 2 with the reason and the
    build command, so a person who ran assay by hand knows no check happened.
    """
    write(tmp_path, "index.html",
          '<script type="module" src="/src/main.jsx"></script>')
    write(tmp_path, "src/main.jsx", "export default 1")
    write(tmp_path, "package.json", "{}")

    code = main([str(tmp_path)])
    said = capsys.readouterr()

    assert code == 2
    assert "build step" in said.err
    assert "npm run build" in said.err


def test_a_page_is_split_into_the_folder_and_the_page(tmp_path: Path) -> None:
    """`assay ./todo.html` opens `todo.html` in its folder, instead of looking
    for `todo.html/index.html`."""
    write(tmp_path, "todo.html", "<!doctype html><body><h1>hi</h1>")

    assert aimed(str(tmp_path / "todo.html"), "index.html") == (
        tmp_path, "todo.html")


def test_a_page_that_was_never_written_is_still_a_page(
        tmp_path: Path) -> None:
    """The `.html` suffix decides the split, even for a file that doesn't
    exist, so the error for a missing page names the page."""
    assert aimed(str(tmp_path / "nope.html"), "index.html") == (
        tmp_path, "nope.html")


def test_a_folder_is_never_split(tmp_path: Path) -> None:
    """A folder is opened as a folder, even when its name ends in `.html`."""
    (tmp_path / "site.html").mkdir()
    write(tmp_path, "site.html/index.html", "<!doctype html><body>hi")

    assert aimed(str(tmp_path / "site.html"), "index.html") == (
        tmp_path / "site.html", "index.html")


def test_a_missing_page_is_named_rather_than_a_folder_under_it(
        tmp_path: Path, capsys) -> None:
    """Running assay on a missing page reports the page as missing, not
    `nope.html/index.html`."""
    code = main([str(tmp_path / "nope.html")])
    said = capsys.readouterr()

    assert code == 2
    assert said.err.strip().endswith("nope.html doesn't exist")
    assert "nope.html/index.html" not in said.err


def test_the_json_carries_what_the_page_logged_as_information() -> None:
    """The JSON includes console errors and failed requests as information.
    They don't decide whether the page works, but they're often the first
    thing to read when a check fails.
    """
    import json
    from types import SimpleNamespace

    from assay.cli import as_json

    run = SimpleNamespace(plan=[], results={}, works=True, surface=None,
                          console_errors=["Uncaught TypeError: x"],
                          failed_requests=["app.js -> HTTP 404"])

    said = json.loads(as_json(run, "todo.html"))

    assert said["entry"] == "todo.html"
    assert said["console_errors"] == ["Uncaught TypeError: x"]
    assert said["failed_requests"] == ["app.js -> HTTP 404"]
    assert said["works"] is True


def test_a_repeat_names_the_first_of_its_group_by_its_words() -> None:
    """`--one-line` prints no case ids, so a repeat names the first finding
    by its action instead of `C003`."""
    from types import SimpleNamespace

    from assay.cli import one_line
    from assay.links import Link
    from assay.qa import FAILED
    from assay.surface import Case

    first = SimpleNamespace(case=Case(id="C003", what="click blue twice"),
                            outcome=FAILED, detail="it stayed lit", links=[])
    again = SimpleNamespace(case=Case(id="C005", what="click green twice"),
                            outcome=FAILED, detail="it stayed lit",
                            links=[Link("same", "C003", "same finding as C003")])
    run = SimpleNamespace(plan=[first.case, again.case],
                          results={"C003": first, "C005": again})

    said = one_line(run, Path("tags"), "index.html").splitlines()

    assert said[1] == "  - click blue twice: it stayed lit"
    assert said[2] == "  - click green twice (same finding as click blue twice)"


def test_if_page_names_a_page_it_could_not_check_for_want_of_a_browser(
        tmp_path: Path, capsys, monkeypatch) -> None:
    """Without Chromium, `--if-page` still exits 0 so a hook doesn't fail the
    turn, but it names the unchecked page on stdout. A hook passes on only
    stdout, and silence would look like a clean page."""
    import assay.cli as cli

    write(tmp_path, "index.html", "<!doctype html><body><button>Go</button>")
    monkeypatch.setattr(cli, "ensure_browser", lambda: False)

    code = main([str(tmp_path), "--if-page", "--one-line"])
    said = capsys.readouterr()

    assert code == 0
    assert said.out == (
        f"assay: couldn't check {tmp_path.name}/index.html because Chromium "
        f"isn't installed and assay couldn't install it, so nothing was "
        f"verified.\n")


def test_a_run_without_the_sandbox_says_so(
        tmp_path: Path, capsys, monkeypatch) -> None:
    """The warning goes to stderr, so the one-line report an agent repeats
    stays one line."""
    from types import SimpleNamespace

    import assay
    import assay.cli as cli

    write(tmp_path, "index.html", "<!doctype html><body>hi")
    monkeypatch.setattr(cli, "ensure_browser", lambda: True)
    run = SimpleNamespace(plan=[], results={}, works=True, sandboxed=False)
    monkeypatch.setattr(assay, "check", lambda *a, **kw: run)

    code = main([str(tmp_path), "--one-line"])
    said = capsys.readouterr()

    assert code == 0
    assert said.err.strip() == cli.SANDBOX_OFF
    assert cli.SANDBOX_OFF not in said.out


def test_the_json_says_whether_the_page_ran_in_the_sandbox() -> None:
    import json
    from types import SimpleNamespace

    from assay.cli import as_json

    run = SimpleNamespace(plan=[], results={}, works=True, surface=None,
                          sandboxed=False)

    assert json.loads(as_json(run))["sandboxed"] is False


def ran(*codes: int):
    """A stand-in for `subprocess.run` that returns `codes` in turn and
    records each command."""
    from types import SimpleNamespace

    left, seen = list(codes), []

    def run(cmd, **kw):
        seen.append(cmd)
        return SimpleNamespace(returncode=left.pop(0))

    return run, seen


def test_an_installed_browser_is_not_downloaded_again(
        capsys, monkeypatch) -> None:
    import assay.cli as cli

    run, seen = ran(0)
    monkeypatch.setattr(cli.subprocess, "run", run)

    assert cli.ensure_browser() is True
    assert len(seen) == 1
    assert capsys.readouterr().err == ""


def test_a_missing_browser_is_downloaded_and_said_so(
        capsys, monkeypatch) -> None:
    import assay.cli as cli

    run, seen = ran(1, 0)
    monkeypatch.setattr(cli.subprocess, "run", run)

    assert cli.ensure_browser() is True
    assert seen[1][1:] == ["-m", "playwright", "install", "chromium"]
    assert "downloading it" in capsys.readouterr().err


def test_a_failed_download_means_no_browser(monkeypatch) -> None:
    import assay.cli as cli

    run, _ = ran(1, 1)
    monkeypatch.setattr(cli.subprocess, "run", run)

    assert cli.ensure_browser() is False
