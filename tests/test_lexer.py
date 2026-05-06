"""Lexer tests for the all-Japanese DSL surface."""

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
    assert kinds("色見本 花 花束 書出") == [
        TokenKind.IROMIHON,
        TokenKind.HANA,
        TokenKind.HANATABA,
        TokenKind.KAKIDASHI,
        TokenKind.EOF,
    ]


def test_compound_property_keywords() -> None:
    assert kinds("花弁数 花弁幅 花弁丈 花弁反り 花弁切込") == [
        TokenKind.KAKEN_SU,
        TokenKind.KAKEN_HABA,
        TokenKind.KAKEN_TAKE,
        TokenKind.KAKEN_SORI,
        TokenKind.KAKEN_KIRIKOMI,
        TokenKind.EOF,
    ]


def test_punctuation_and_canvas_separator() -> None:
    assert kinds("{}();, ×") == [
        TokenKind.LBRACE,
        TokenKind.RBRACE,
        TokenKind.LPAREN,
        TokenKind.RPAREN,
        TokenKind.SEMI,
        TokenKind.COMMA,
        TokenKind.TIMES,
        TokenKind.EOF,
    ]


def test_number_with_japanese_suffixes() -> None:
    tokens = tokenize("42 3.14 12点 50% 90度 0.25周")
    assert tokens[0].kind == TokenKind.NUMBER and tokens[0].value == 42.0
    assert tokens[1].kind == TokenKind.NUMBER and tokens[1].value == 3.14
    assert tokens[2].kind == TokenKind.PIXEL and tokens[2].value == 12.0
    assert tokens[3].kind == TokenKind.PERCENT and tokens[3].value == 0.5
    assert tokens[4].kind == TokenKind.DEG and tokens[4].value == 90.0
    assert tokens[5].kind == TokenKind.TURN and tokens[5].value == 0.25


def test_unknown_numeric_suffix_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("12秒")


def test_range_operator() -> None:
    assert kinds("12..32") == [
        TokenKind.NUMBER,
        TokenKind.DOTDOT,
        TokenKind.NUMBER,
        TokenKind.EOF,
    ]


def test_palette_dot_reference_lexes_three_tokens() -> None:
    tokens = tokenize("春.桜色")
    assert [t.kind for t in tokens] == [
        TokenKind.IDENT,
        TokenKind.DOT,
        TokenKind.IDENT,
        TokenKind.EOF,
    ]
    assert tokens[0].lexeme == "春"
    assert tokens[2].lexeme == "桜色"


def test_japanese_identifier_with_digits() -> None:
    tokens = tokenize("さくら500 五百")
    assert tokens[0].kind == TokenKind.IDENT and tokens[0].lexeme == "さくら500"
    assert tokens[1].kind == TokenKind.IDENT and tokens[1].lexeme == "五百"


def test_komejirushi_starts_a_line_comment() -> None:
    tokens = tokenize("※ これはコメント\n花 さくら")
    assert tokens[0].kind == TokenKind.HANA
    assert tokens[0].line == 2


def test_string_with_path_keeps_alphabet_in_data() -> None:
    tokens = tokenize('"hero.svg"')
    assert tokens[0].kind == TokenKind.STRING
    assert tokens[0].value == "hero.svg"


def test_alphabet_outside_string_is_rejected() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("bloom")


def test_unterminated_string_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize('"unclosed')


def test_unknown_character_raises() -> None:
    with pytest.raises(FlorasSyntaxError):
        tokenize("@")


def test_chikaku_iro_lexes_as_keyword() -> None:
    tokens = tokenize("知覚色(0.78 0.13 12)")
    assert tokens[0].kind == TokenKind.CHIKAKU_IRO


def test_negative_number() -> None:
    tokens = tokenize("(-50, -30)")
    assert tokens[0].kind == TokenKind.LPAREN
    assert tokens[1].kind == TokenKind.NUMBER
    assert tokens[1].value == -50.0
    assert tokens[3].kind == TokenKind.NUMBER
    assert tokens[3].value == -30.0


def test_motif_keyword_lexes() -> None:
    tokens = tokenize("模様 ひとえだ {}")
    assert tokens[0].kind == TokenKind.MOYOU
    assert tokens[1].kind == TokenKind.IDENT and tokens[1].lexeme == "ひとえだ"
