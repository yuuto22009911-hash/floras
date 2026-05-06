"""Parser tests."""

from __future__ import annotations

import pytest

from floras.ast_nodes import (
    BloomDecl,
    HexColor,
    NumberValue,
    OklchColor,
    PaletteDecl,
    PaletteRef,
    Program,
    Range,
    StrokeSpec,
)
from floras.errors import FlorasSyntaxError
from floras.lexer import tokenize
from floras.parser import Parser


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse_program()


def test_minimal_bloom_decl() -> None:
    p = parse("bloom sakura { petals 5; size 200; color #FFB7C5; }")
    assert len(p.blooms) == 1
    bloom = p.blooms[0]
    assert isinstance(bloom, BloomDecl)
    assert bloom.name == "sakura"
    assert bloom.properties["petals"] == NumberValue(value=5.0, line=1)
    assert isinstance(bloom.properties["color"], HexColor)
    assert bloom.properties["color"].hex == "#FFB7C5"


def test_palette_decl() -> None:
    src = (
        "palette brand { primary #FFB7C5; 500 oklch(0.78 0.13 12); ink #2C2825; }"
    )
    p = parse(src)
    assert len(p.palettes) == 1
    pal = p.palettes[0]
    assert isinstance(pal, PaletteDecl)
    assert pal.name == "brand"
    primary = pal.tokens["primary"]
    assert isinstance(primary, HexColor) and primary.hex == "#FFB7C5"
    assert isinstance(pal.tokens["500"], OklchColor)
    ink = pal.tokens["ink"]
    assert isinstance(ink, HexColor) and ink.hex == "#2C2825"


def test_palette_reference_in_bloom() -> None:
    src = "palette b { primary #FFB7C5; }\nbloom s { color b.primary; }"
    p = parse(src)
    bloom = p.blooms[0]
    color = bloom.properties["color"]
    assert isinstance(color, PaletteRef)
    assert color.palette == "b"
    assert color.token == "primary"


def test_palette_reference_with_tint() -> None:
    src = "bloom s { color brand.500 tinted brand.50 0.3; }"
    p = parse(src)
    color = p.blooms[0].properties["color"]
    assert isinstance(color, PaletteRef)
    assert color.tint_palette == "brand"
    assert color.tint_token == "50"
    assert color.tint_amount == 0.3


def test_stroke_property() -> None:
    p = parse("bloom s { stroke #2C2825 width 1.5; }")
    spec = p.blooms[0].properties["stroke"]
    assert isinstance(spec, StrokeSpec)
    assert isinstance(spec.color, HexColor)
    assert spec.color.hex == "#2C2825"
    assert spec.width == 1.5


def test_range_in_value_position_is_parsed() -> None:
    p = parse("bloom s { size 12..32; }")
    val = p.blooms[0].properties["size"]
    assert isinstance(val, Range)
    assert val.min == 12.0 and val.max == 32.0


def test_export_decl() -> None:
    p = parse('bloom s { petals 5; }\nexport s to "out.svg";')
    assert len(p.exports) == 1
    assert p.exports[0].target == "s"
    assert p.exports[0].path == "out.svg"


def test_duplicate_property_in_bloom_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("bloom s { petals 5; petals 8; }")


def test_duplicate_palette_token_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("palette b { primary #FFF; primary #000; }")


def test_unexpected_top_level_token_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("petals 5;")


def test_missing_semicolon_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("bloom s { petals 5 }")


def test_oklch_in_value_position() -> None:
    p = parse("bloom s { color oklch(0.78 0.13 12); }")
    color = p.blooms[0].properties["color"]
    assert isinstance(color, OklchColor)
    assert color.l == 0.78 and color.c == 0.13 and color.h == 12.0
