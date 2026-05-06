"""Symbol & colour resolution. Converts AST values into concrete primitives."""

from __future__ import annotations

import math
from typing import Any

from floras.ast_nodes import (
    AngleValue,
    BloomDecl,
    BoolValue,
    ColorValue,
    HexColor,
    IdentValue,
    NumberValue,
    OklchColor,
    PaletteDecl,
    PaletteRef,
    PercentValue,
    Range,
    StrokeSpec,
    Value,
)
from floras.compose.scene import BloomInstance
from floras.errors import FlorasNameError, FlorasValidationError

_INK = HexColor(hex="#2C2825")
_PINK = HexColor(hex="#FFB7C5")
_LEAF_GREEN = HexColor(hex="#4A7C59")


# Keys whose default values fill out a BloomInstance when the user omits them.
_BLOOM_DEFAULTS: dict[str, Any] = {
    "petals": 5,
    "size": 200.0,
    "color": _PINK,
    "rotation": 0.0,
    "petal-width": None,    # derived from size if absent
    "petal-height": None,   # derived from size if absent
    "petal-curl": 0.4,
    "petal-notch": 0.0,
    "stamen-count": 12,
    "stamen-radius": None,  # derived from size if absent
    "stamen-color": _INK,
    "stem": False,
    "stem-length": None,    # derived from size if absent
    "stem-color": _LEAF_GREEN,
    "leaf-count": 0,
    "arrange": "ring",
}


def build_palette_table(palettes: dict[str, PaletteDecl]) -> dict[str, dict[str, HexColor]]:
    """Resolve every palette token to a HexColor (oklch → sRGB if needed)."""
    out: dict[str, dict[str, HexColor]] = {}
    for name, decl in palettes.items():
        out[name] = {tok: _color_to_hex(value, palettes={}) for tok, value in decl.tokens.items()}
    return out


def resolve_bloom(
    decl: BloomDecl, palettes: dict[str, dict[str, HexColor]]
) -> BloomInstance:
    """Merge declaration properties with defaults and validate them."""

    def _val(key: str) -> Any:
        if key in decl.properties:
            v = decl.properties[key]
            if isinstance(v, StrokeSpec):
                return v
            return _value_to_native(v, palettes)
        return _BLOOM_DEFAULTS[key]

    petals = int(_val("petals"))
    if petals < 1:
        raise FlorasValidationError(decl.line, "'petals' must be at least 1")

    size = float(_val("size"))
    if size <= 0.0:
        raise FlorasValidationError(decl.line, "'size' must be positive")

    rotation_raw = _val("rotation")
    rotation = _coerce_angle(rotation_raw, decl.line)

    petal_width_raw = _val("petal-width")
    petal_width = float(petal_width_raw) if petal_width_raw is not None else size * 0.20
    petal_height_raw = _val("petal-height")
    petal_height = float(petal_height_raw) if petal_height_raw is not None else size * 0.42

    curl = float(_val("petal-curl"))
    if not 0.0 <= curl <= 1.0:
        raise FlorasValidationError(decl.line, "'petal-curl' must be in [0, 1]")
    notch = float(_val("petal-notch"))
    if not 0.0 <= notch <= 1.0:
        raise FlorasValidationError(decl.line, "'petal-notch' must be in [0, 1]")

    stamen_count = int(_val("stamen-count"))
    if stamen_count < 0:
        raise FlorasValidationError(decl.line, "'stamen-count' must be >= 0")
    stamen_radius_raw = _val("stamen-radius")
    stamen_radius = (
        float(stamen_radius_raw) if stamen_radius_raw is not None else size * 0.025
    )

    stem_flag = bool(_val("stem"))
    stem_length_raw = _val("stem-length")
    stem_length = (
        float(stem_length_raw) if stem_length_raw is not None else size * 0.6
    )

    leaf_count = int(_val("leaf-count"))
    if leaf_count < 0:
        raise FlorasValidationError(decl.line, "'leaf-count' must be >= 0")

    arrange_value = _val("arrange")
    arrange_name = (
        arrange_value.name if isinstance(arrange_value, IdentValue) else str(arrange_value)
    )
    if arrange_name not in {"ring", "spiral"}:
        raise FlorasValidationError(
            decl.line, f"'arrange' must be 'ring' or 'spiral', got '{arrange_name}'"
        )

    color_value = _val("color")
    if not isinstance(color_value, HexColor):
        raise FlorasValidationError(decl.line, "'color' must resolve to a colour")
    stamen_color = _val("stamen-color")
    if not isinstance(stamen_color, HexColor):
        raise FlorasValidationError(decl.line, "'stamen-color' must resolve to a colour")
    stem_color = _val("stem-color")
    if not isinstance(stem_color, HexColor):
        raise FlorasValidationError(decl.line, "'stem-color' must resolve to a colour")

    stroke_color: HexColor | None = None
    stroke_width: float = 0.0
    if "stroke" in decl.properties:
        spec = decl.properties["stroke"]
        if not isinstance(spec, StrokeSpec):
            raise FlorasValidationError(
                decl.line, "'stroke' must be specified as `<color> width <number>`"
            )
        stroke_color = _color_to_hex(spec.color, palettes)
        stroke_width = spec.width

    arrange_rotation = 137.508 if arrange_name == "spiral" else 360.0 / petals

    return BloomInstance(
        bloom_name=decl.name,
        x=0.0,
        y=0.0,
        size=size,
        rotation=rotation,
        color=color_value,
        petals=petals,
        petal_width=petal_width,
        petal_height=petal_height,
        petal_curl=curl,
        petal_notch=notch,
        stamen_count=stamen_count,
        stamen_radius=stamen_radius,
        stamen_color=stamen_color,
        stem=stem_flag,
        stem_length=stem_length,
        stem_color=stem_color,
        leaf_count=leaf_count,
        arrange=arrange_name,
        arrange_rotation=arrange_rotation,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
    )


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------


def _value_to_native(value: Value, palettes: dict[str, dict[str, HexColor]]) -> Any:
    if isinstance(value, NumberValue):
        return value.value
    if isinstance(value, PercentValue):
        return value.value
    if isinstance(value, AngleValue):
        return value.degrees
    if isinstance(value, BoolValue):
        return value.value
    if isinstance(value, IdentValue):
        return value
    if isinstance(value, HexColor):
        return value
    if isinstance(value, OklchColor):
        return _oklch_to_hex(value)
    if isinstance(value, PaletteRef):
        return _resolve_palette_ref(value, palettes)
    if isinstance(value, Range):
        # A range cannot resolve to a single value at this stage; ranges only
        # make sense inside a scatter, which v0.1.0 does not yet implement.
        raise FlorasValidationError(
            value.line, "ranges (a..b) are only valid inside scatter blocks"
        )
    raise FlorasValidationError(0, f"unsupported value: {value}")


def _coerce_angle(value: Any, line: int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise FlorasValidationError(line, f"expected an angle, got {value!r}")


def _color_to_hex(value: ColorValue, palettes: dict[str, dict[str, HexColor]]) -> HexColor:
    if isinstance(value, HexColor):
        return value
    if isinstance(value, OklchColor):
        return _oklch_to_hex(value)
    if isinstance(value, PaletteRef):
        return _resolve_palette_ref(value, palettes)
    raise FlorasValidationError(0, f"unsupported colour value: {value}")


def _resolve_palette_ref(
    ref: PaletteRef, palettes: dict[str, dict[str, HexColor]]
) -> HexColor:
    if ref.palette not in palettes:
        raise FlorasNameError(ref.line, f"palette '{ref.palette}' is not defined")
    table = palettes[ref.palette]
    if ref.token not in table:
        raise FlorasNameError(
            ref.line, f"palette token '{ref.palette}.{ref.token}' is not defined"
        )
    base = table[ref.token]
    if ref.tint_palette is None:
        return base
    if ref.tint_palette not in palettes:
        raise FlorasNameError(
            ref.line, f"palette '{ref.tint_palette}' (used in tint) is not defined"
        )
    tint_table = palettes[ref.tint_palette]
    assert ref.tint_token is not None
    if ref.tint_token not in tint_table:
        raise FlorasNameError(
            ref.line,
            f"palette token '{ref.tint_palette}.{ref.tint_token}' (used in tint) is not defined",
        )
    tint = tint_table[ref.tint_token]
    return _blend_hex(base, tint, ref.tint_amount)


# ---------------------------------------------------------------------------
# Colour conversions
# ---------------------------------------------------------------------------


def _hex_to_rgb(h: HexColor) -> tuple[int, int, int]:
    s = h.hex.lstrip("#")
    if len(s) == 8:
        s = s[:6]
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> HexColor:
    return HexColor(hex=f"#{r:02X}{g:02X}{b:02X}")


def _blend_hex(a: HexColor, b: HexColor, amount: float) -> HexColor:
    if not 0.0 <= amount <= 1.0:
        raise FlorasValidationError(0, "tint amount must be in [0, 1]")
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        round(ar * (1 - amount) + br * amount),
        round(ag * (1 - amount) + bg * amount),
        round(ab * (1 - amount) + bb * amount),
    )


def _oklch_to_hex(c: OklchColor) -> HexColor:
    """Convert OKLCH to sRGB hex. Standard-library-only implementation."""
    lightness = c.l
    a = c.c * math.cos(math.radians(c.h))
    b = c.c * math.sin(math.radians(c.h))

    # OKLab → linear sRGB (Björn Ottosson, 2020)
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b

    l3 = l_ ** 3
    m3 = m_ ** 3
    s3 = s_ ** 3

    r_lin = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g_lin = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    b_lin = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3

    def _gamma(x: float) -> int:
        x = max(0.0, min(1.0, x))
        if x <= 0.0031308:
            v = 12.92 * x
        else:
            v = 1.055 * (x ** (1 / 2.4)) - 0.055
        return round(v * 255)

    return _rgb_to_hex(_gamma(r_lin), _gamma(g_lin), _gamma(b_lin))
