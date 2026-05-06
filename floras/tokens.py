"""Token definitions for the Floras language (v0.1.0 Core)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TokenKind(StrEnum):
    # Literals / atoms
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"

    # Declarations / control flow
    SAKURA = "sakura"        # let
    YURI = "yuri"            # fn
    BARA = "bara"            # if
    TSUBAKI = "tsubaki"      # else
    UME = "ume"              # while
    RAN = "ran"              # return
    HIMAWARI = "himawari"    # import (reserved, v0.1.0 unused)

    # Comment marker — the lexer consumes `shion ...` to end-of-line; this kind
    # exists only so that `shion` cannot accidentally be used as an identifier.
    SHION = "shion"

    # Literals (boolean / null)
    HASU = "hasu"            # true
    ASAGAO = "asagao"        # false
    TANPOPO = "tanpopo"      # null

    # Builtin functions
    BOTAN = "botan"          # print
    AYAME = "ayame"          # input

    # Brackets
    KOBUSHI = "kobushi"      # (
    MOKUREN = "mokuren"      # )
    AJISAI = "ajisai"        # {
    KIKYOU = "kikyou"        # }
    KOSUMOSU = "kosumosu"    # [ (reserved)
    DAHLIA = "dahlia"        # ] (reserved)

    # Punctuation
    NADESHIKO = "nadeshiko"  # ;
    KASUMI = "kasumi"        # ,

    # Assignment / comparison / arithmetic / logical
    TSUYUKUSA = "tsuyukusa"        # =
    WASURENAGUSA = "wasurenagusa"  # ==
    AZAMI = "azami"                # !=
    FUKUJUSOU = "fukujusou"        # <
    TACHIAOI = "tachiaoi"          # >
    SUIREN = "suiren"              # <=
    SHOBU = "shobu"                # >=
    MOMO = "momo"                  # +
    KEITOU = "keitou"              # - (binary and unary)
    MARIGOLD = "marigold"          # *
    SUZURAN = "suzuran"            # /
    RENGE = "renge"                # %
    SUMIRE = "sumire"              # &&
    PANSY = "pansy"                # ||
    KESHI = "keshi"                # !

    # String literal pair (D-02 / ADR-11)
    BARA_KUCHI = "bara_kuchi"
    BARA_TOJIRU = "bara_tojiru"

    # Meta
    EOF = "EOF"


KEYWORDS: Final[dict[str, TokenKind]] = {
    k.value: k
    for k in TokenKind
    if k.value
    not in {
        "NUMBER",
        "STRING",
        "IDENT",
        "EOF",
    }
}
"""Mapping from source lexeme to TokenKind. Used by the lexer to classify
identifiers either as keywords or as user identifiers (TokenKind.IDENT)."""


BINARY_OPS: Final[frozenset[TokenKind]] = frozenset(
    {
        TokenKind.MOMO,
        TokenKind.KEITOU,
        TokenKind.MARIGOLD,
        TokenKind.SUZURAN,
        TokenKind.RENGE,
        TokenKind.WASURENAGUSA,
        TokenKind.AZAMI,
        TokenKind.FUKUJUSOU,
        TokenKind.TACHIAOI,
        TokenKind.SUIREN,
        TokenKind.SHOBU,
        TokenKind.SUMIRE,
        TokenKind.PANSY,
    }
)


UNARY_OPS: Final[frozenset[TokenKind]] = frozenset(
    {TokenKind.KESHI, TokenKind.KEITOU}
)


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    col: int
    value: object = None
