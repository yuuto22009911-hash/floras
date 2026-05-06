"""Palette → CSS / Tailwind / JSON exporter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from floras.ast_nodes import PaletteDecl
from floras.cli import main
from floras.lexer import tokenize
from floras.parser import Parser
from floras.renderers.css import render_css, render_json, render_tailwind

SRC = (
    "色見本 春 {\n"
    "  桜色 知覚色(0.85 0.10 12);\n"
    "  墨   知覚色(0.20 0.02 30);\n"
    "}\n"
    "色見本 秋 {\n"
    "  紅葉 知覚色(0.55 0.18 25);\n"
    "}\n"
)


def _palettes(src: str = SRC) -> list[PaletteDecl]:
    return Parser(tokenize(src)).parse_program().palettes


def test_render_css_emits_root_block_with_japanese_var_names() -> None:
    out = render_css(_palettes())
    assert ":root {" in out
    assert "}" in out.rstrip().splitlines()[-1]
    # All four tokens should be present.
    assert "--春-桜色: #" in out
    assert "--春-墨: #" in out
    assert "--秋-紅葉: #" in out


def test_render_tailwind_emits_theme_block_with_color_prefix() -> None:
    out = render_tailwind(_palettes())
    assert "@theme {" in out
    assert "--color-春-桜色: #" in out
    assert "--color-秋-紅葉: #" in out


def test_render_json_is_nested_and_round_trips() -> None:
    out = render_json(_palettes())
    parsed = json.loads(out)
    assert set(parsed) == {"春", "秋"}
    assert set(parsed["春"]) == {"桜色", "墨"}
    assert parsed["春"]["桜色"].startswith("#")
    assert parsed["秋"]["紅葉"].startswith("#")


def test_render_with_no_palettes_is_empty() -> None:
    css = render_css([])
    assert ":root {\n}" in css
    js = render_json([])
    assert json.loads(js) == {}


def test_palette_oklch_to_hex_is_deterministic() -> None:
    a = render_css(_palettes())
    b = render_css(_palettes())
    assert a == b


def test_cli_tokens_to_stdout_default_css(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "春.bloom"
    src.write_text(SRC, encoding="utf-8")
    rc = main(["tokens", str(src)])
    captured = capsys.readouterr()
    assert rc == 0
    assert ":root {" in captured.out
    assert "--春-桜色: #" in captured.out


def test_cli_tokens_with_format_tailwind(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "春.bloom"
    src.write_text(SRC, encoding="utf-8")
    rc = main(["tokens", str(src), "--format", "tailwind"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "@theme {" in captured.out


def test_cli_tokens_with_format_json_writes_to_out(tmp_path: Path) -> None:
    src = tmp_path / "春.bloom"
    src.write_text(SRC, encoding="utf-8")
    out = tmp_path / "tokens.json"
    rc = main(
        ["tokens", str(src), "--out", str(out), "--format", "json"]
    )
    assert rc == 0
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["春"]["桜色"].startswith("#")


def test_cli_tokens_missing_file_returns_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["tokens", "見つからない.bloom"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "file not found" in captured.err


def test_cli_tokens_syntax_error_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "壊れた.bloom"
    src.write_text("色見本 春 {", encoding="utf-8")
    rc = main(["tokens", str(src)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Floras SyntaxError" in captured.err
