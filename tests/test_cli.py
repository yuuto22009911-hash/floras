"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from floras.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
SAKURA = EXAMPLES / "桜.bloom"


def test_render_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["render", str(SAKURA)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.startswith("<svg ")


def test_render_writes_out_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "桜.svg"
    rc = main(["render", str(SAKURA), "--out", str(out)])
    assert rc == 0
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<svg ")


def test_render_missing_file_returns_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["render", "見つからない.bloom"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "file not found" in captured.err


def test_render_syntax_error_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.bloom"
    bad.write_text("花 桜 { 花弁数 5", encoding="utf-8")
    rc = main(["render", str(bad)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Floras SyntaxError" in captured.err


def test_render_with_ast_flag_outputs_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["render", str(SAKURA), "--ast"])
    captured = capsys.readouterr()
    assert rc == 0
    assert '"type": "Program"' in captured.out
