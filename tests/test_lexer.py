"""Lexer tests — covers all v0.1.0 token kinds and string/comment handling."""

from __future__ import annotations

import pytest

from floras.errors import FlorasSyntaxError
from floras.lexer import tokenize
from floras.tokens import TokenKind


def kinds(source: str) -> list[TokenKind]:
    return [t.kind for t in tokenize(source)]


def test_empty_source_emits_only_eof() -> None:
    assert kinds("") == [TokenKind.EOF]


def test_keywords_are_recognised() -> None:
    src = "sakura yuri bara tsubaki ume ran botan ayame hasu asagao tanpopo"
    expected = [
        TokenKind.SAKURA,
        TokenKind.YURI,
        TokenKind.BARA,
        TokenKind.TSUBAKI,
        TokenKind.UME,
        TokenKind.RAN,
        TokenKind.BOTAN,
        TokenKind.AYAME,
        TokenKind.HASU,
        TokenKind.ASAGAO,
        TokenKind.TANPOPO,
        TokenKind.EOF,
    ]
    assert kinds(src) == expected


def test_brackets_punctuation_assignment() -> None:
    src = "kobushi mokuren ajisai kikyou kosumosu dahlia nadeshiko kasumi tsuyukusa"
    assert kinds(src) == [
        TokenKind.KOBUSHI,
        TokenKind.MOKUREN,
        TokenKind.AJISAI,
        TokenKind.KIKYOU,
        TokenKind.KOSUMOSU,
        TokenKind.DAHLIA,
        TokenKind.NADESHIKO,
        TokenKind.KASUMI,
        TokenKind.TSUYUKUSA,
        TokenKind.EOF,
    ]


def test_comparison_arithmetic_logical() -> None:
    src = (
        "wasurenagusa azami fukujusou tachiaoi suiren shobu "
        "momo keitou marigold suzuran renge sumire pansy keshi"
    )
    assert kinds(src) == [
        TokenKind.WASURENAGUSA,
        TokenKind.AZAMI,
        TokenKind.FUKUJUSOU,
        TokenKind.TACHIAOI,
        TokenKind.SUIREN,
        TokenKind.SHOBU,
        TokenKind.MOMO,
        TokenKind.KEITOU,
        TokenKind.MARIGOLD,
        TokenKind.SUZURAN,
        TokenKind.RENGE,
        TokenKind.SUMIRE,
        TokenKind.PANSY,
        TokenKind.KESHI,
        TokenKind.EOF,
    ]


def test_identifier_classification() -> None:
    tokens = tokenize("foo bar123 _baz")
    assert [t.kind for t in tokens] == [
        TokenKind.IDENT,
        TokenKind.IDENT,
        TokenKind.IDENT,
        TokenKind.EOF,
    ]
    assert tokens[0].lexeme == "foo"
    assert tokens[1].lexeme == "bar123"
    assert tokens[2].lexeme == "_baz"


def test_integer_and_float_numbers() -> None:
    tokens = tokenize("42 3.14 0")
    assert tokens[0].kind == TokenKind.NUMBER and tokens[0].value == 42
    assert tokens[1].kind == TokenKind.NUMBER and tokens[1].value == 3.14
    assert tokens[2].kind == TokenKind.NUMBER and tokens[2].value == 0


def test_string_literal_basic() -> None:
    tokens = tokenize("bara_kuchi world bara_tojiru")
    assert tokens[0].kind == TokenKind.STRING
    assert tokens[0].value == "world"


def test_string_literal_with_internal_spaces() -> None:
    tokens = tokenize("bara_kuchi Hello,  bara_tojiru")
    assert tokens[0].value == "Hello, "


def test_unterminated_string_is_an_error() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("bara_kuchi oops")


def test_line_comment_is_skipped() -> None:
    tokens = tokenize("shion this is a comment\nsakura x tsuyukusa 1 nadeshiko")
    # The comment line should not contribute tokens; we should see the let
    # statement on line 2.
    assert tokens[0].kind == TokenKind.SAKURA
    assert tokens[0].line == 2


def test_unknown_character_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("@")


def test_line_and_column_tracking() -> None:
    tokens = tokenize("sakura\n  yuri")
    assert tokens[0].line == 1 and tokens[0].col == 1
    assert tokens[1].line == 2 and tokens[1].col == 3
