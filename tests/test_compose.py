"""Compose / resolver tests."""

from __future__ import annotations

from typing import Any

import pytest

from floras.compose import compose
from floras.compose.resolver import _oklch_to_hex
from floras.compose.scene import Scene
from floras.errors import FlorasNameError, FlorasValidationError
from floras.lexer import tokenize
from floras.parser import Parser


def _scene(source: str, **kwargs: Any) -> Scene:
    return compose(Parser(tokenize(source)).parse_program(), **kwargs)


def test_minimal_bloom_produces_scene_with_one_instance() -> None:
    scene = _scene("bloom s { petals 5; size 200; color #FFB7C5; }")
    assert len(scene.items) == 1
    inst = scene.items[0]
    assert inst.bloom_name == "s"
    assert inst.size == 200.0
    assert inst.color.hex == "#FFB7C5"


def test_palette_reference_resolves() -> None:
    scene = _scene(
        "palette brand { primary #FFB7C5; }\n"
        "bloom s { petals 5; size 200; color brand.primary; }"
    )
    assert scene.items[0].color.hex == "#FFB7C5"


def test_palette_token_unknown_raises_name_error() -> None:
    src = (
        "palette brand { primary #FFB7C5; }\n"
        "bloom s { color brand.missing; }"
    )
    with pytest.raises(FlorasNameError):
        _scene(src)


def test_palette_unknown_raises_name_error() -> None:
    src = "bloom s { color phantom.500; }"
    with pytest.raises(FlorasNameError):
        _scene(src)


def test_palette_tint_blends_two_colors() -> None:
    scene = _scene(
        "palette b { primary #FF0000; paper #FFFFFF; }\n"
        "bloom s { color b.primary tinted b.paper 0.5; }"
    )
    # 50% blend of #FF0000 with #FFFFFF → #FF8080
    assert scene.items[0].color.hex == "#FF8080"


def test_invalid_petals_raises_validation_error() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("bloom s { petals 0; }")


def test_invalid_petal_curl_raises() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("bloom s { petal-curl 1.5; }")


def test_no_bloom_raises() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("palette b { primary #FFF; }")


def test_explicit_entry_selects_named_bloom() -> None:
    scene = _scene(
        "bloom a { petals 4; }\nbloom b { petals 7; }",
        entry="b",
    )
    assert scene.items[0].bloom_name == "b"
    assert scene.items[0].petals == 7


def test_unknown_entry_raises_name_error() -> None:
    with pytest.raises(FlorasNameError):
        _scene("bloom a { petals 4; }", entry="missing")


def test_multiple_blooms_without_entry_raises() -> None:
    with pytest.raises(FlorasValidationError):
        _scene("bloom a { petals 4; }\nbloom b { petals 7; }")


def test_bouquet_renders_with_canvas_size_and_background() -> None:
    src = (
        "bloom s { petals 5; size 200; color #FFB7C5; }\n"
        "bouquet hero {\n"
        "  canvas 1200 x 630;\n"
        "  background #FAF7F2;\n"
        "  place s at (300, 315);\n"
        "  place s at (900, 315);\n"
        "}"
    )
    scene = _scene(src)
    assert scene.canvas == (1200.0, 630.0)
    assert scene.background is not None and scene.background.hex == "#FAF7F2"
    assert len(scene.items) == 2


def test_bouquet_place_at_center_resolves_to_canvas_centre() -> None:
    src = (
        "bloom s { petals 5; size 200; color #FFB7C5; }\n"
        "bouquet hero {\n"
        "  canvas 1000 x 600;\n"
        "  place s at center;\n"
        "}"
    )
    scene = _scene(src)
    inst = scene.items[0]
    assert inst.x == 500.0 and inst.y == 300.0


def test_bouquet_placement_overrides_take_priority_over_bloom_decl() -> None:
    src = (
        "bloom s { petals 5; size 200; color #FFB7C5; }\n"
        "bouquet hero {\n"
        "  canvas 600 x 600;\n"
        "  place s at center { size 80; color #FF0000; };\n"
        "}"
    )
    inst = _scene(src).items[0]
    assert inst.size == 80.0
    assert inst.color.hex == "#FF0000"


def test_bouquet_with_unknown_bloom_raises_name_error() -> None:
    src = (
        "bouquet hero {\n"
        "  canvas 600 x 600;\n"
        "  place ghost at center;\n"
        "}"
    )
    with pytest.raises(FlorasNameError):
        _scene(src)


def test_single_bouquet_is_default_entry_with_helper_blooms() -> None:
    src = (
        "bloom s { petals 5; }\n"
        "bloom t { petals 8; }\n"
        "bouquet hero { canvas 400 x 400; place s at center; }"
    )
    scene = _scene(src)
    assert scene.canvas == (400.0, 400.0)
    assert scene.items[0].bloom_name == "s"


def test_oklch_red_converts_to_recognisable_hex() -> None:
    from floras.ast_nodes import OklchColor

    out = _oklch_to_hex(OklchColor(l=0.628, c=0.258, h=29.0))
    # OKLCH red ~ #FF0000 within rounding tolerance
    assert out.hex.startswith("#FF") or out.hex.startswith("#FE")


def test_spiral_arrange_uses_golden_angle() -> None:
    scene = _scene("bloom rose { petals 24; arrange spiral; }")
    inst = scene.items[0]
    assert inst.arrange == "spiral"
    assert abs(inst.arrange_rotation - 137.508) < 0.01
