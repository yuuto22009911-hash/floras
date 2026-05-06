"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from floras.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_run_hello_returns_zero_and_prints_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["run", str(EXAMPLES / "hello.floras")])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.rstrip("\n") == "Hello, world"


def test_run_missing_file_returns_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["run", "no-such-file.floras"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "file not found" in captured.err


def test_run_syntax_error_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.floras"
    bad.write_text("sakura x tsuyukusa 1\n", encoding="utf-8")  # missing nadeshiko
    rc = main(["run", str(bad)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Floras SyntaxError" in captured.err


def test_run_with_ast_flag_emits_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["run", str(EXAMPLES / "hello.floras"), "--ast"])
    captured = capsys.readouterr()
    assert rc == 0
    assert '"type": "Program"' in captured.out
