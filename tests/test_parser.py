"""Parser tests for the all-Japanese DSL."""

from __future__ import annotations

import pytest

from floras.ast_nodes import (
    AreaCanvas,
    AreaGrid,
    AreaRing,
    BloomDecl,
    NumberValue,
    OklchColor,
    PaletteDecl,
    PaletteRef,
    Program,
    Range,
    ScatterDecl,
    StrokeSpec,
)
from floras.errors import FlorasSyntaxError
from floras.lexer import tokenize
from floras.parser import Parser


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse_program()


def test_minimal_bloom_decl() -> None:
    p = parse("花 桜 { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }")
    assert len(p.blooms) == 1
    bloom = p.blooms[0]
    assert isinstance(bloom, BloomDecl)
    assert bloom.name == "桜"
    assert bloom.properties["花弁数"] == NumberValue(value=5.0, line=1)
    color = bloom.properties["色"]
    assert isinstance(color, OklchColor) and color.l == 0.85


def test_palette_decl_with_oklch_entries() -> None:
    src = "色見本 春 { 桜色 知覚色(0.85 0.10 12); 墨 知覚色(0.20 0.02 30); }"
    p = parse(src)
    pal = p.palettes[0]
    assert isinstance(pal, PaletteDecl)
    assert pal.name == "春"
    sakura = pal.tokens["桜色"]
    assert isinstance(sakura, OklchColor)


def test_palette_reference_in_bloom() -> None:
    src = "色見本 春 { 桜色 知覚色(0.85 0.10 12); }\n花 桜 { 色 春.桜色; }"
    p = parse(src)
    color = p.blooms[0].properties["色"]
    assert isinstance(color, PaletteRef)
    assert color.palette == "春" and color.token == "桜色"


def test_palette_reference_with_tinted() -> None:
    src = "花 桜 { 色 春.桜色 混ぜ 春.紙 0.3; }"
    p = parse(src)
    color = p.blooms[0].properties["色"]
    assert isinstance(color, PaletteRef)
    assert color.tint_palette == "春"
    assert color.tint_token == "紙"
    assert color.tint_amount == 0.3


def test_stroke_property_with_japanese_width() -> None:
    p = parse("花 桜 { 輪郭 知覚色(0.20 0.02 30) 幅 1.5; }")
    spec = p.blooms[0].properties["輪郭"]
    assert isinstance(spec, StrokeSpec)
    assert isinstance(spec.color, OklchColor)
    assert spec.width == 1.5


def test_range_in_value_position() -> None:
    p = parse("花 桜 { 大きさ 12..32; }")
    val = p.blooms[0].properties["大きさ"]
    assert isinstance(val, Range)
    assert val.min == 12.0 and val.max == 32.0


def test_export_uses_he_keyword() -> None:
    p = parse('花 桜 { 花弁数 5; }\n書出 桜 へ "out.svg";')
    assert p.exports[0].target == "桜"
    assert p.exports[0].path == "out.svg"


def test_bouquet_decl_with_canvas_separator() -> None:
    src = (
        "花 桜 { 花弁数 5; }\n"
        "花束 ヒーロー {\n"
        "  画布 1200 × 630;\n"
        "  背景 知覚色(0.97 0.01 80);\n"
        "  置く 桜 に 中央;\n"
        "}"
    )
    p = parse(src)
    bq = p.bouquets[0]
    assert bq.name == "ヒーロー"
    assert bq.canvas_width == 1200.0
    assert bq.canvas_height == 630.0
    assert len(bq.placements) == 1
    assert bq.placements[0].coord.is_center


def test_bouquet_place_at_explicit_coord() -> None:
    src = "花 桜 { 花弁数 5; } 花束 束 { 画布 600 × 600; 置く 桜 に (300, 300); }"
    p = parse(src)
    place = p.bouquets[0].placements[0]
    assert place.coord.x == 300.0 and place.coord.y == 300.0


def test_bouquet_placement_with_overrides() -> None:
    src = (
        "花 桜 { 花弁数 5; }\n"
        "花束 束 { 画布 600 × 600; 置く 桜 に 中央 { 大きさ 80; 回転 30度; }; }"
    )
    p = parse(src)
    place = p.bouquets[0].placements[0]
    assert "大きさ" in place.overrides
    assert "回転" in place.overrides


def test_scatter_with_canvas_area_and_ranges() -> None:
    src = (
        "花 花弁 { 花弁数 5; }\n"
        "花束 束 {\n"
        "  画布 1200 × 630;\n"
        "  散らす {\n"
        "    元 花弁;\n"
        "    数 60;\n"
        "    領域 画布;\n"
        "    大きさ 16..56;\n"
        "    回転 乱数;\n"
        "    種 42;\n"
        "  }\n"
        "}"
    )
    p = parse(src)
    sc = p.bouquets[0].scatters[0]
    assert isinstance(sc, ScatterDecl)
    assert sc.source == "花弁"
    assert sc.count == 60
    assert sc.seed == 42
    assert isinstance(sc.area, AreaCanvas)
    assert isinstance(sc.size, Range)


def test_scatter_with_ring_area() -> None:
    src = (
        "花 花弁 { 花弁数 5; }\n"
        "花束 束 {\n"
        "  画布 1000 × 1000;\n"
        "  散らす {\n"
        "    元 花弁; 数 12;\n"
        "    領域 輪 中央 (500, 500) 内 200 外 320;\n"
        "    種 7;\n"
        "  }\n"
        "}"
    )
    p = parse(src)
    sc = p.bouquets[0].scatters[0]
    assert isinstance(sc.area, AreaRing)
    assert sc.area.center_x == 500.0 and sc.area.outer == 320.0


def test_scatter_with_grid_area_and_jidou_count() -> None:
    src = (
        "花 花弁 { 花弁数 5; }\n"
        "花束 束 {\n"
        "  画布 600 × 400;\n"
        "  散らす { 元 花弁; 数 自動; 領域 格子 列 6 行 4; 種 1; }\n"
        "}"
    )
    p = parse(src)
    sc = p.bouquets[0].scatters[0]
    assert sc.count == "自動"
    assert isinstance(sc.area, AreaGrid)
    assert sc.area.cols == 6 and sc.area.rows == 4


def test_scatter_without_seed_raises() -> None:
    src = (
        "花 花弁 { 花弁数 5; }\n"
        "花束 束 { 画布 600 × 600; 散らす { 元 花弁; 数 4; 領域 画布; } }"
    )
    with pytest.raises(FlorasSyntaxError):
        parse(src)


def test_duplicate_property_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("花 桜 { 花弁数 5; 花弁数 8; }")


def test_unexpected_top_level_token_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("花弁数 5;")


def test_missing_semicolon_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("花 桜 { 花弁数 5 }")
