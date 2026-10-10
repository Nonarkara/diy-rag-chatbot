"""Smoke test — the tool runs, --help works, hello sub-command works."""
from cli import main
from my_tool import hello, version_info


def test_version_info_is_string():
    assert isinstance(version_info(), str)


def test_hello_default():
    assert hello() == "hello, world 👋"


def test_hello_named():
    assert hello("claude") == "hello, claude 👋"


def test_main_help_returns_zero():
    assert main(["--help"]) == 0


def test_main_hello_returns_zero(capsys):
    assert main(["hello", "--name", "vibecoder"]) == 0
    captured = capsys.readouterr()
    assert "hello, vibecoder" in captured.out
