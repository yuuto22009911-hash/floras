"""AST node definitions for the Floras Bloom DSL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

# ---------------------------------------------------------------------------
# Value types — primitive literals and references that appear as property values
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NumberValue:
    value: float
    line: int = 0


@dataclass(frozen=True)
class PercentValue:
    """A percentage literal — value already converted (50% → 0.5)."""

    value: float
    line: int = 0


@dataclass(frozen=True)
class AngleValue:
    """An angle in degrees (`90deg`) or turns (`0.25turn`, normalised to deg)."""

    degrees: float
    line: int = 0


@dataclass(frozen=True)
class Range:
    """An inclusive numeric range used by scatter properties (`12..32`)."""

    min: float
    max: float
    line: int = 0


@dataclass(frozen=True)
class HexColor:
    """An RGB (or RGBA) colour, normalised to `#RRGGBB` or `#RRGGBBAA`."""

    hex: str
    line: int = 0


@dataclass(frozen=True)
class OklchColor:
    l: float
    c: float
    h: float
    line: int = 0


@dataclass(frozen=True)
class PaletteRef:
    palette: str
    token: str
    tint_palette: str | None = None
    tint_token: str | None = None
    tint_amount: float = 0.0
    line: int = 0


@dataclass(frozen=True)
class IdentValue:
    """A bare identifier reference — `center`, `auto`, `random`, or user names."""

    name: str
    line: int = 0


@dataclass(frozen=True)
class BoolValue:
    value: bool
    line: int = 0


@dataclass(frozen=True)
class StringValue:
    value: str
    line: int = 0


Value: TypeAlias = (
    NumberValue
    | PercentValue
    | AngleValue
    | Range
    | HexColor
    | OklchColor
    | PaletteRef
    | IdentValue
    | BoolValue
    | StringValue
)
ColorValue: TypeAlias = HexColor | OklchColor | PaletteRef


# ---------------------------------------------------------------------------
# Top-level declarations
# ---------------------------------------------------------------------------


@dataclass
class PaletteDecl:
    name: str
    tokens: dict[str, ColorValue]
    line: int = 0


@dataclass
class StrokeSpec:
    color: ColorValue
    width: float
    line: int = 0


@dataclass
class BloomDecl:
    name: str
    properties: dict[str, Value | StrokeSpec] = field(default_factory=dict)
    line: int = 0


@dataclass
class Program:
    palettes: list[PaletteDecl] = field(default_factory=list)
    blooms: list[BloomDecl] = field(default_factory=list)
    bouquets: list[BouquetDecl] = field(default_factory=list)
    exports: list[ExportDecl] = field(default_factory=list)
    line: int = 1


@dataclass
class ExportDecl:
    target: str
    path: str
    line: int = 0


@dataclass(frozen=True)
class Coord:
    """A 2D coordinate, either explicit (x, y) or the symbolic `center`."""

    x: float | None = None
    y: float | None = None
    is_center: bool = False
    line: int = 0


@dataclass
class Placement:
    target: str
    coord: Coord
    overrides: dict[str, Value | StrokeSpec] = field(default_factory=dict)
    line: int = 0


@dataclass
class BouquetDecl:
    name: str
    canvas_width: float = 0.0
    canvas_height: float = 0.0
    background: ColorValue | None = None
    placements: list[Placement] = field(default_factory=list)
    line: int = 0
