"""Lexer: turn `.bloom` source text into a list of tokens.

Identifiers are made up of CJK Han / Hiragana / Katakana characters (with the
katakana long-mark `ー` and middle-dot `・`), optionally extended with ASCII
digits in continuation. ASCII alphabetic characters are not part of the
language surface and trigger a syntax error if encountered outside of a
string literal or a comment.
"""

from __future__ import annotations

from floras.errors import FlorasSyntaxError
from floras.tokens import KEYWORDS, Token, TokenKind

_DIGITS = "0123456789"

_NUMERIC_SUFFIXES: dict[str, TokenKind] = {
    "点": TokenKind.PIXEL,
    "度": TokenKind.DEG,
    "周": TokenKind.TURN,
}


def _is_ident_start(ch: str) -> bool:
    code = ord(ch)
    if 0x3041 <= code <= 0x3096:  # Hiragana letters
        return True
    if 0x30A1 <= code <= 0x30FA:  # Katakana letters
        return True
    if ch in ("ー", "・"):  # katakana long-mark / middle-dot used inside names
        return True
    if 0x4E00 <= code <= 0x9FFF:  # CJK Unified Ideographs (Han)
        return True
    if 0x3400 <= code <= 0x4DBF:  # CJK Unified Ideographs Extension A
        return True
    return False


def _is_ident_cont(ch: str) -> bool:
    return _is_ident_start(ch) or ch in _DIGITS


class _Lexer:
    def __init__(self, source: str) -> None:
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while not self._at_end():
            ch = self._peek()
            if ch.isspace():
                self._advance()
                continue
            if ch == "※":
                self._consume_comment()
                continue
            if ch == "×":
                self._read_single_punct(TokenKind.TIMES)
                continue
            if ch in _DIGITS:
                self._read_number()
                continue
            if ch == "-" and self._next_is_digit():
                self._read_number(negative=True)
                continue
            if ch == ".":
                self._read_dot()
                continue
            if _is_ident_start(ch):
                self._read_identifier_or_keyword()
                continue
            if ch == '"':
                self._read_string()
                continue
            if ch in "{}();,":
                self._read_punct(ch)
                continue
            # ASCII alphabet is intentionally rejected to enforce the
            # all-Japanese surface (not even hex / English keywords leak in).
            raise FlorasSyntaxError(self.line, f"unexpected character {ch!r}")
        self.tokens.append(Token(TokenKind.EOF, "", self.line, self.col))
        return self.tokens

    # ---- character classes / punct -----------------------------------------

    def _consume_comment(self) -> None:
        # `※ ... \n` — discard up to (and including) end of line.
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _read_single_punct(self, kind: TokenKind) -> None:
        line, col = self.line, self.col
        lexeme = self._advance()
        self.tokens.append(Token(kind, lexeme, line, col))

    def _read_punct(self, ch: str) -> None:
        line, col = self.line, self.col
        kind_map = {
            "{": TokenKind.LBRACE,
            "}": TokenKind.RBRACE,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            ";": TokenKind.SEMI,
            ",": TokenKind.COMMA,
        }
        self._advance()
        self.tokens.append(Token(kind_map[ch], ch, line, col))

    def _read_dot(self) -> None:
        line, col = self.line, self.col
        if self.pos + 1 < len(self.src) and self.src[self.pos + 1] == ".":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenKind.DOTDOT, "..", line, col))
            return
        self._advance()
        self.tokens.append(Token(TokenKind.DOT, ".", line, col))

    # ---- identifiers / keywords --------------------------------------------

    def _read_identifier_or_keyword(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        while not self._at_end() and _is_ident_cont(self._peek()):
            self._advance()
        lexeme = self.src[start_pos : self.pos]

        kind = KEYWORDS.get(lexeme)
        if kind is None:
            self.tokens.append(Token(TokenKind.IDENT, lexeme, start_line, start_col))
            return
        # If the matched lexeme is also a numeric suffix (`点` `度` `周`) and we
        # land here it means the suffix appeared as a standalone identifier.
        # The numeric reader already absorbs valid suffixes, so a bare suffix
        # word can be treated as a normal keyword/identifier — we just emit the
        # keyword token. (This branch is mostly future-proofing.)
        self.tokens.append(Token(kind, lexeme, start_line, start_col))

    # ---- numbers ------------------------------------------------------------

    def _next_is_digit(self) -> bool:
        return self.pos + 1 < len(self.src) and self.src[self.pos + 1] in _DIGITS

    def _read_number(self, *, negative: bool = False) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        if negative:
            self._advance()  # consume leading '-'
        while not self._at_end() and self._peek() in _DIGITS:
            self._advance()
        is_float = False
        if (
            not self._at_end()
            and self._peek() == "."
            and self.pos + 1 < len(self.src)
            and self.src[self.pos + 1] in _DIGITS
        ):
            is_float = True
            self._advance()
            while not self._at_end() and self._peek() in _DIGITS:
                self._advance()

        lexeme = self.src[start_pos : self.pos]
        value: float = float(lexeme) if is_float else float(int(lexeme))

        # Suffixes: `12点`, `50%`, `90度`, `0.25周`. The `%` sign is one byte
        # of pure punctuation; the others are single CJK characters.
        kind = TokenKind.NUMBER
        if not self._at_end() and self._peek() == "%":
            self._advance()
            kind = TokenKind.PERCENT
            value = value / 100.0
            lexeme = self.src[start_pos : self.pos]
        elif not self._at_end() and self._peek() in _NUMERIC_SUFFIXES:
            suffix = self._peek()
            self._advance()
            kind = _NUMERIC_SUFFIXES[suffix]
            lexeme = self.src[start_pos : self.pos]
        elif not self._at_end() and _is_ident_start(self._peek()):
            # An unknown CJK character glued to a number is more useful as an
            # explicit error than as silent identifier merging.
            suffix_start = self.pos
            while not self._at_end() and _is_ident_cont(self._peek()):
                self._advance()
            suffix = self.src[suffix_start : self.pos]
            raise FlorasSyntaxError(
                start_line, f"unknown numeric suffix: {suffix!r}"
            )

        self.tokens.append(
            Token(kind, lexeme, start_line, start_col, value=value)
        )

    # ---- strings ------------------------------------------------------------

    def _read_string(self) -> None:
        start_line, start_col = self.line, self.col
        self._advance()  # consume opening "
        buf: list[str] = []
        while not self._at_end() and self._peek() != '"':
            ch = self._peek()
            if ch == "\\" and self.pos + 1 < len(self.src):
                nxt = self.src[self.pos + 1]
                if nxt in ('"', "\\"):
                    buf.append(nxt)
                    self._advance()
                    self._advance()
                    continue
            buf.append(ch)
            self._advance()
        if self._at_end():
            raise FlorasSyntaxError(start_line, "unterminated string literal")
        self._advance()  # consume closing "
        self.tokens.append(
            Token(
                TokenKind.STRING,
                f'"{"".join(buf)}"',
                start_line,
                start_col,
                value="".join(buf),
            )
        )

    # ---- low-level cursor ---------------------------------------------------

    def _peek(self) -> str:
        return self.src[self.pos]

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _at_end(self) -> bool:
        return self.pos >= len(self.src)


def tokenize(source: str) -> list[Token]:
    return _Lexer(source).tokenize()
