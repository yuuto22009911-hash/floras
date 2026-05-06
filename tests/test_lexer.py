"""Lexer tests."""

from __future__ import annotations

import pytest

from floras.errors import FlorasSyntaxError
from floras.lexer import tokenize
from floras.tokens import TokenKind


def kinds(source: str) -> list[TokenKind]:
    return [t.kind for t in tokenize(source)]


def test_empty_source_emits_only_eof() -> None:
    assert kinds("") == [TokenKind.EOF]


def test_top_level_keywords() -> None:
    assert kinds("palette bloom motif bouquet export") == [
        TokenKind.PALETTE,
        TokenKind.BLOOM,
        TokenKind.MOTIF,
        TokenKind.BOUQUET,
        TokenKind.EXPORT,
        TokenKind.EOF,
    ]


def test_kebab_case_property_keywords() -> None:
    assert kinds("petal-width petal-height petal-curl petal-notch") == [
        TokenKind.PETAL_WIDTH,
        TokenKind.PETAL_HEIGHT,
        TokenKind.PETAL_CURL,
        TokenKind.PETAL_NOTCH,
        TokenKind.EOF,
    ]


def test_punctuation() -> None:
    assert kinds("{}();,") == [
        TokenKind.LBRACE,
        TokenKind.RBRACE,
        TokenKind.LPAREN,
        TokenKind.RPAREN,
        TokenKind.SEMI,
        TokenKind.COMMA,
        TokenKind.EOF,
    ]


def test_number_and_suffixes() -> None:
    tokens = tokenize("42 3.14 12px 50% 90deg 0.25turn")
    assert tokens[0].kind == TokenKind.NUMBER and tokens[0].value == 42.0
    assert tokens[1].kind == TokenKind.NUMBER and tokens[1].value == 3.14
    assert tokens[2].kind == TokenKind.PIXEL and tokens[2].value == 12.0
    assert tokens[3].kind == TokenKind.PERCENT and tokens[3].value == 0.5
    assert tokens[4].kind == TokenKind.DEG and tokens[4].value == 90.0
    assert tokens[5].kind == TokenKind.TURN and tokens[5].value == 0.25


def test_unknown_numeric_suffix_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("12rad")


def test_hex_color_three_six_eight_digits() -> None:
    tokens = tokenize("#FFB #FFB7C5 #FFB7C5AA")
    assert tokens[0].kind == TokenKind.HEX_COLOR and tokens[0].value == "#FFFFBB"
    assert tokens[1].kind == TokenKind.HEX_COLOR and tokens[1].value == "#FFB7C5"
    assert tokens[2].kind == TokenKind.HEX_COLOR and tokens[2].value == "#FFB7C5AA"


def test_invalid_hex_length_raises() -> None:
    # 5-digit hex is invalid; only 3, 4, 6, 8 digits are accepted.
    with pytest.raises(FlorasSyntaxError):
        tokenize("#FFB7C")


def test_range_operator() -> None:
    tokens = tokenize("12..32")
    assert [t.kind for t in tokens] == [
        TokenKind.NUMBER,
        TokenKind.DOTDOT,
        TokenKind.NUMBER,
        TokenKind.EOF,
    ]


def test_palette_dot_reference_is_lexed_as_three_tokens() -> None:
    tokens = tokenize("brand.500")
    assert [t.kind for t in tokens] == [
        TokenKind.IDENT,
        TokenKind.DOT,
        TokenKind.NUMBER,
        TokenKind.EOF,
    ]
    assert tokens[0].lexeme == "brand"


def test_string_literal_with_escape() -> None:
    tokens = tokenize(r'"hello\\ \"world\""')
    assert tokens[0].kind == TokenKind.STRING
    assert tokens[0].value == r'hello\ "world"'


def test_unterminated_string_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize('"unclosed')


def test_line_comment_skipped_and_line_count_advances() -> None:
    tokens = tokenize("shion top comment\nbloom sakura")
    assert tokens[0].kind == TokenKind.BLOOM
    assert tokens[0].line == 2


def test_unknown_character_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("@")
