"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from floras.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_render_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["render", str(EXAMPLES / "sakura.bloom")])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.startswith("<svg ")


def test_render_writes_out_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sakura.svg"
    rc = main(["render", str(EXAMPLES / "sakura.bloom"), "--out", str(out)])
    assert rc == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<svg ")


def test_render_missing_file_returns_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["render", "no-such.bloom"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "file not found" in captured.err


def test_render_syntax_error_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.bloom"
    bad.write_text("bloom s { petals 5", encoding="utf-8")
    rc = main(["render", str(bad)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Floras SyntaxError" in captured.err


def test_render_with_ast_flag_outputs_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["render", str(EXAMPLES / "sakura.bloom"), "--ast"])
    captured = capsys.readouterr()
    assert rc == 0
    assert '"type": "Program"' in captured.out


def test_render_with_explicit_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "two.bloom"
    src.write_text(
        "bloom a { petals 4; }\nbloom b { petals 7; }\n", encoding="utf-8"
    )
    rc = main(["render", str(src), "--entry", "b"])
    captured = capsys.readouterr()
    assert rc == 0
    # 7-petal bloom emits 7 petal <path>s.
    assert captured.out.count("<path") >= 7
