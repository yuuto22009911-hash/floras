"""Lexer: turn `.bloom` source text into a list of tokens."""

from __future__ import annotations

from floras.errors import FlorasSyntaxError
from floras.tokens import KEYWORDS, Token, TokenKind

_IDENT_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_IDENT_CONT = _IDENT_START + "0123456789-"
_DIGITS = "0123456789"
_HEX = "0123456789abcdefABCDEF"

_NUMERIC_SUFFIXES: dict[str, TokenKind] = {
    "px": TokenKind.PIXEL,
    "deg": TokenKind.DEG,
    "turn": TokenKind.TURN,
}


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
            if ch == "#":
                self._read_hex_color()
            elif ch in _DIGITS:
                self._read_number()
            elif ch == ".":
                self._read_dot()
            elif ch in _IDENT_START:
                self._read_identifier_or_keyword()
            elif ch == '"':
                self._read_string()
            elif ch in "{}();,":
                self._read_punct(ch)
            else:
                raise FlorasSyntaxError(self.line, f"unexpected character {ch!r}")
        self.tokens.append(Token(TokenKind.EOF, "", self.line, self.col))
        return self.tokens

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
        # `..` range operator vs single `.` (palette dot reference).
        if self.pos + 1 < len(self.src) and self.src[self.pos + 1] == ".":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenKind.DOTDOT, "..", line, col))
            return
        self._advance()
        self.tokens.append(Token(TokenKind.DOT, ".", line, col))

    def _read_identifier_or_keyword(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        while not self._at_end() and self._peek() in _IDENT_CONT:
            self._advance()
        # Identifiers must not end with a hyphen (`stem-` is invalid).
        if self.src[self.pos - 1] == "-":
            raise FlorasSyntaxError(
                start_line,
                f"identifier cannot end with '-': {self.src[start_pos:self.pos]!r}",
            )
        lexeme = self.src[start_pos : self.pos]

        if lexeme == "shion":
            # Line comment: consume to end-of-line. The `shion` keyword itself
            # is not emitted as a token.
            while not self._at_end() and self._peek() != "\n":
                self._advance()
            return

        # Numeric suffixes like `12px` are handled in _read_number; if a bare
        # identifier matches a known suffix here it is just a regular keyword
        # mismatch and falls through to KEYWORDS lookup or IDENT.

        kind = KEYWORDS.get(lexeme, TokenKind.IDENT)
        self.tokens.append(Token(kind, lexeme, start_line, start_col))

    def _read_number(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        while not self._at_end() and self._peek() in _DIGITS:
            self._advance()
        is_float = False
        # A '.' followed by a digit (and not another '.') is a fractional part.
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

        # Look for a numeric suffix: `12px`, `50%`, `90deg`, `0.25turn`.
        kind = TokenKind.NUMBER
        if not self._at_end() and self._peek() == "%":
            self._advance()
            kind = TokenKind.PERCENT
            value = value / 100.0
            lexeme = self.src[start_pos : self.pos]
        elif not self._at_end() and self._peek() in _IDENT_START:
            suffix_start = self.pos
            while not self._at_end() and self._peek() in _IDENT_CONT:
                self._advance()
            suffix = self.src[suffix_start : self.pos]
            if suffix in _NUMERIC_SUFFIXES:
                kind = _NUMERIC_SUFFIXES[suffix]
                lexeme = self.src[start_pos : self.pos]
            else:
                raise FlorasSyntaxError(
                    start_line, f"unknown numeric suffix: {suffix!r}"
                )

        self.tokens.append(
            Token(kind, lexeme, start_line, start_col, value=value)
        )

    def _read_hex_color(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        self._advance()  # consume '#'
        digits_start = self.pos
        while not self._at_end() and self._peek() in _HEX:
            self._advance()
        digits = self.src[digits_start : self.pos]
        if len(digits) not in (3, 4, 6, 8):
            raise FlorasSyntaxError(
                start_line,
                f"hex color must have 3, 4, 6, or 8 digits, got {len(digits)}",
            )
        lexeme = self.src[start_pos : self.pos]
        # Normalise to 6 or 8 hex chars (#RGB → #RRGGBB).
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        elif len(digits) == 4:
            digits = "".join(c * 2 for c in digits)
        normalised = "#" + digits.upper()
        self.tokens.append(
            Token(TokenKind.HEX_COLOR, lexeme, start_line, start_col, value=normalised)
        )

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
