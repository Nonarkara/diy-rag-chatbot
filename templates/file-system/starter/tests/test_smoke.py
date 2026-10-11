"""Smoke test — the tool runs, --help works, hello sub-command works."""
from cli import main
from my_tool import hello, version_info


def test_version_info_is_string():
    assert isinstance(version_info(), str)


def test_hello_default():
    assert hello() == "hello, world 👋"


def test_hello_named():
    assert hello("vibecoder") == "hello, vibecoder 👋"


def test_main_help_returns_zero(capsys):
    # --help calls SystemExit; argparse --version is the canonical way
    # for a version flag. Here we just confirm the parser doesn't error.
    with __import__("pytest").raises(SystemExit):
        main(["--help"])
    captured = capsys.readouterr()
    assert "my-tool" in captured.out or "usage" in captured.out.lower()


def test_main_hello_returns_zero(capsys):
    assert main(["hello", "--name", "vibecoder"]) == 0
    captured = capsys.readouterr()
    assert "hello, vibecoder" in captured.out
