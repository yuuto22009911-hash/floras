"""Compose / resolver tests for the all-Japanese DSL."""

from __future__ import annotations

from typing import Any

import pytest

from floras.compose import compose
from floras.compose.resolver import _oklch_to_hex
from floras.compose.scene import Scene
from floras.errors import FlorasNameError, FlorasSyntaxError, FlorasValidationError
from floras.lexer import tokenize
from floras.parser import Parser


def _scene(source: str, **kwargs: Any) -> Scene:
    return compose(Parser(tokenize(source)).parse_program(), **kwargs)


def test_minimal_bloom_produces_scene_with_one_instance() -> None:
    scene = _scene("花 桜 { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }")
    assert len(scene.items) == 1
    inst = scene.items[0]
    assert inst.bloom_name == "桜"
    assert inst.size == 200.0


def test_palette_reference_resolves_to_hex() -> None:
    scene = _scene(
        "色見本 春 { 桜色 知覚色(0.85 0.10 12); }\n"
        "花 桜 { 大きさ 200; 色 春.桜色; }"
    )
    assert scene.items[0].color.hex.startswith("#")


def test_palette_token_unknown_raises() -> None:
    src = "色見本 春 { 桜色 知覚色(0.85 0.10 12); }\n花 桜 { 色 春.見つからない; }"
    with pytest.raises(FlorasNameError):
        _scene(src)


def test_unknown_palette_raises() -> None:
    with pytest.raises(FlorasNameError):
        _scene("花 桜 { 色 幻.桜色; }")


def test_invalid_petals_raises_validation() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("花 桜 { 花弁数 0; }")


def test_invalid_curl_raises() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("花 桜 { 花弁反り 1.5; }")


def test_no_bloom_raises() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("色見本 春 { 桜色 知覚色(0.85 0.10 12); }")


def test_explicit_entry_selects_named_bloom() -> None:
    scene = _scene(
        "花 甲 { 花弁数 4; }\n花 乙 { 花弁数 7; }",
        entry="乙",
    )
    assert scene.items[0].bloom_name == "乙"
    assert scene.items[0].petals == 7


def test_unknown_entry_raises() -> None:
    with pytest.raises(FlorasNameError):
        _scene("花 桜 { 花弁数 5; }", entry="幻")


def test_bouquet_renders_with_canvas_size_and_background() -> None:
    src = (
        "花 桜 { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }\n"
        "花束 ヒーロー {\n"
        "  画布 1200 × 630;\n"
        "  背景 知覚色(0.97 0.01 80);\n"
        "  置く 桜 に (300, 315);\n"
        "  置く 桜 に (900, 315);\n"
        "}"
    )
    scene = _scene(src)
    assert scene.canvas == (1200.0, 630.0)
    assert scene.background is not None
    assert len(scene.items) == 2


def test_bouquet_at_center_resolves_to_canvas_centre() -> None:
    src = (
        "花 桜 { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }\n"
        "花束 束 { 画布 1000 × 600; 置く 桜 に 中央; }"
    )
    scene = _scene(src)
    inst = scene.items[0]
    assert inst.x == 500.0 and inst.y == 300.0


def test_scatter_canvas_produces_deterministic_positions() -> None:
    src = (
        "花 花弁 { 花弁数 5; 大きさ 80; 色 知覚色(0.85 0.10 12); }\n"
        "花束 束 {\n"
        "  画布 1200 × 630;\n"
        "  散らす { 元 花弁; 数 24; 領域 画布; 種 42; }\n"
        "}"
    )
    a = _scene(src)
    b = _scene(src)
    assert len(a.items) == 24
    assert all(av == bv for av, bv in zip(a.items, b.items, strict=True))


def test_scatter_grid_uses_grid_cells() -> None:
    src = (
        "花 花弁 { 花弁数 5; 大きさ 60; 色 知覚色(0.85 0.10 12); }\n"
        "花束 束 {\n"
        "  画布 600 × 400;\n"
        "  散らす { 元 花弁; 数 自動; 領域 格子 列 6 行 4; 種 1; }\n"
        "}"
    )
    scene = _scene(src)
    assert len(scene.items) == 24


def test_scatter_size_range_samples_within_range() -> None:
    src = (
        "花 花弁 { 花弁数 5; 大きさ 50; 色 知覚色(0.85 0.10 12); }\n"
        "花束 束 {\n"
        "  画布 1000 × 1000;\n"
        "  散らす { 元 花弁; 数 30; 領域 画布; 大きさ 16..56; 種 99; }\n"
        "}"
    )
    scene = _scene(src)
    for inst in scene.items:
        assert 16.0 <= inst.size <= 56.0


def test_scatter_unknown_source_raises() -> None:
    src = (
        "花束 束 { 画布 600 × 600; 散らす { 元 幻; 数 4; 領域 画布; 種 1; } }"
    )
    with pytest.raises(FlorasNameError):
        _scene(src)


def test_scatter_seed_required_raises_at_parse_time() -> None:
    src = (
        "花 花弁 { 花弁数 5; }\n"
        "花束 束 { 画布 600 × 600; 散らす { 元 花弁; 数 4; 領域 画布; } }"
    )
    with pytest.raises(FlorasSyntaxError):
        _scene(src)


def test_oklch_red_converts_to_recognisable_hex() -> None:
    from floras.ast_nodes import OklchColor

    out = _oklch_to_hex(OklchColor(l=0.628, c=0.258, h=29.0))
    assert out.hex.startswith("#FF") or out.hex.startswith("#FE")


def test_spiral_arrange_uses_golden_angle() -> None:
    scene = _scene("花 薔薇 { 花弁数 24; 並び 螺旋; 色 知覚色(0.62 0.18 12); }")
    inst = scene.items[0]
    assert inst.arrange == "螺旋"
    assert abs(inst.arrange_rotation - 137.508) < 0.01
