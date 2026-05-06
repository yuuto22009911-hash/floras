"""Token definitions for the Floras Bloom DSL (v0.1.0)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TokenKind(StrEnum):
    # Atoms / literals
    NUMBER = "NUMBER"
    PIXEL = "PIXEL"          # 12px
    PERCENT = "PERCENT"      # 50%
    DEG = "DEG"              # 90deg
    TURN = "TURN"            # 0.25turn
    HEX_COLOR = "HEX_COLOR"  # #FFB7C5 / #FFB7C5AA
    STRING = "STRING"        # "..."
    IDENT = "IDENT"

    # Punctuation
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    SEMI = ";"
    COMMA = ","
    DOT = "."
    DOTDOT = ".."

    # Top-level keywords
    PALETTE = "palette"
    BLOOM = "bloom"
    MOTIF = "motif"
    BOUQUET = "bouquet"
    EXPORT = "export"

    # Statement keywords
    CANVAS = "canvas"
    BACKGROUND = "background"
    PLACE = "place"
    AT = "at"
    SCATTER = "scatter"
    SOURCE = "source"
    COUNT = "count"
    AREA = "area"
    SEED = "seed"
    SIZE = "size"
    ROTATION = "rotation"
    COLOR = "color"
    STROKE = "stroke"
    WIDTH = "width"
    HEIGHT = "height"
    FROM = "from"
    TO = "to"
    PETALS = "petals"
    PETAL_WIDTH = "petal-width"
    PETAL_HEIGHT = "petal-height"
    PETAL_CURL = "petal-curl"
    PETAL_NOTCH = "petal-notch"
    STAMEN_COUNT = "stamen-count"
    STAMEN_RADIUS = "stamen-radius"
    STAMEN_COLOR = "stamen-color"
    STEM = "stem"
    STEM_LENGTH = "stem-length"
    STEM_COLOR = "stem-color"
    LEAF_COUNT = "leaf-count"
    ARRANGE = "arrange"
    TINTED = "tinted"

    # Area sub-keywords
    RING = "ring"
    RECT = "rect"
    GRID = "grid"
    PATH = "path"

    # Arrange sub-keywords
    SPIRAL = "spiral"

    # Built-in constants
    CENTER = "center"
    AUTO = "auto"
    RANDOM = "random"
    TRUE = "true"
    FALSE = "false"
    NONE_KW = "none"

    # Other reserved words
    OKLCH = "oklch"  # function-like literal: `oklch(L C H)`
    COLS = "cols"
    ROWS = "rows"
    INNER = "inner"
    OUTER = "outer"
    X_KW = "x"  # canvas size separator: `1200 x 630`

    # Meta
    EOF = "EOF"


# Lexemes that should resolve to a keyword TokenKind. Identifiers not present
# in this map are emitted as TokenKind.IDENT (ordinary user identifiers).
KEYWORDS: Final[dict[str, TokenKind]] = {
    "palette": TokenKind.PALETTE,
    "bloom": TokenKind.BLOOM,
    "motif": TokenKind.MOTIF,
    "bouquet": TokenKind.BOUQUET,
    "export": TokenKind.EXPORT,
    "canvas": TokenKind.CANVAS,
    "background": TokenKind.BACKGROUND,
    "place": TokenKind.PLACE,
    "at": TokenKind.AT,
    "scatter": TokenKind.SCATTER,
    "source": TokenKind.SOURCE,
    "count": TokenKind.COUNT,
    "area": TokenKind.AREA,
    "seed": TokenKind.SEED,
    "size": TokenKind.SIZE,
    "rotation": TokenKind.ROTATION,
    "color": TokenKind.COLOR,
    "stroke": TokenKind.STROKE,
    "width": TokenKind.WIDTH,
    "height": TokenKind.HEIGHT,
    "from": TokenKind.FROM,
    "to": TokenKind.TO,
    "petals": TokenKind.PETALS,
    "petal-width": TokenKind.PETAL_WIDTH,
    "petal-height": TokenKind.PETAL_HEIGHT,
    "petal-curl": TokenKind.PETAL_CURL,
    "petal-notch": TokenKind.PETAL_NOTCH,
    "stamen-count": TokenKind.STAMEN_COUNT,
    "stamen-radius": TokenKind.STAMEN_RADIUS,
    "stamen-color": TokenKind.STAMEN_COLOR,
    "stem": TokenKind.STEM,
    "stem-length": TokenKind.STEM_LENGTH,
    "stem-color": TokenKind.STEM_COLOR,
    "leaf-count": TokenKind.LEAF_COUNT,
    "arrange": TokenKind.ARRANGE,
    "tinted": TokenKind.TINTED,
    "ring": TokenKind.RING,
    "rect": TokenKind.RECT,
    "grid": TokenKind.GRID,
    "path": TokenKind.PATH,
    "spiral": TokenKind.SPIRAL,
    "center": TokenKind.CENTER,
    "auto": TokenKind.AUTO,
    "random": TokenKind.RANDOM,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "none": TokenKind.NONE_KW,
    "oklch": TokenKind.OKLCH,
    "cols": TokenKind.COLS,
    "rows": TokenKind.ROWS,
    "inner": TokenKind.INNER,
    "outer": TokenKind.OUTER,
    "x": TokenKind.X_KW,
}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    col: int
    value: object = None
