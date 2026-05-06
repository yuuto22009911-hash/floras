"""Token definitions for the Floras Bloom DSL (all-Japanese surface)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class TokenKind(StrEnum):
    # ----- Atoms / literals (internal labels — never appear in source) -----
    NUMBER = "NUMBER"
    PIXEL = "PIXEL"          # 12点
    PERCENT = "PERCENT"      # 50%
    DEG = "DEG"              # 90度
    TURN = "TURN"            # 0.25周
    STRING = "STRING"
    IDENT = "IDENT"

    # ----- Punctuation (no alphabet) -----
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    SEMI = ";"
    COMMA = ","
    DOT = "."
    DOTDOT = ".."
    TIMES = "×"  # canvas separator: 画布 1200 × 630

    # ----- Top-level declarations -----
    IROMIHON = "色見本"      # palette
    HANA = "花"              # bloom
    HANATABA = "花束"        # bouquet
    KAKIDASHI = "書出"       # export
    MOYOU = "模様"           # motif (reserved for v0.5.0)

    # ----- Statement keywords -----
    GAFU = "画布"            # canvas
    HAIKEI = "背景"          # background
    OKU = "置く"             # place
    NI = "に"                # at
    CHIRASU = "散らす"       # scatter
    MOTO = "元"              # source
    KAZU = "数"              # count
    RYOUIKI = "領域"         # area
    TANE = "種"              # seed
    OOKISA = "大きさ"        # size
    KAITEN = "回転"          # rotation
    IRO = "色"               # color (property name)
    CHIKAKU_IRO = "知覚色"   # OKLCH function: 知覚色(L C H)
    RINKAKU = "輪郭"         # stroke
    HABA = "幅"              # width
    TAKASA = "高さ"          # height
    HE = "へ"                # to (export X へ "path")
    KAKEN_SU = "花弁数"      # petals
    KAKEN_HABA = "花弁幅"    # petal-width
    KAKEN_TAKE = "花弁丈"    # petal-height
    KAKEN_SORI = "花弁反り"  # petal-curl
    KAKEN_KIRIKOMI = "花弁切込"  # petal-notch
    OSHIBE_SU = "雄蕊数"     # stamen-count
    OSHIBE_HANKEI = "雄蕊半径"  # stamen-radius
    OSHIBE_IRO = "雄蕊色"    # stamen-color
    KUKI = "茎"              # stem
    KUKI_TAKE = "茎丈"       # stem-length
    KUKI_IRO = "茎色"        # stem-color
    HASU_SU = "葉数"         # leaf-count
    NARABI = "並び"          # arrange
    MAZE = "混ぜ"            # tinted

    # ----- Area sub-keywords -----
    WA = "輪"                # ring  (also 'ring' arrange)
    KUKEI = "矩形"           # rect
    KOUSHI = "格子"          # grid

    # ----- Arrange sub-keywords -----
    RASEN = "螺旋"           # spiral

    # ----- Built-in constants -----
    CHUUOU = "中央"          # center
    JIDOU = "自動"           # auto
    RANSUU = "乱数"          # random
    SHIN = "真"              # true
    GI = "偽"                # false
    MU = "無"                # null

    # ----- Other reserved -----
    RETSU = "列"             # cols
    GYOU = "行"              # rows
    UCHI = "内"              # inner
    SOTO = "外"              # outer

    # ----- Comment marker (consumed by lexer, no token emitted) -----
    KOME = "※"

    # ----- Meta -----
    EOF = "EOF"


# Mapping from source lexeme to TokenKind for keyword recognition.
# Identifiers not present in this map are emitted as TokenKind.IDENT.
KEYWORDS: Final[dict[str, TokenKind]] = {
    k.value: k
    for k in TokenKind
    if k.value
    not in {
        "NUMBER",
        "PIXEL",
        "PERCENT",
        "DEG",
        "TURN",
        "STRING",
        "IDENT",
        "EOF",
        # punctuation/marker tokens are dispatched directly by the lexer,
        # not by keyword lookup.
        "{",
        "}",
        "(",
        ")",
        ";",
        ",",
        ".",
        "..",
        "×",
        "※",
    }
}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    col: int
    value: object = None
