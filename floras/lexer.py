"""Lexer: turn Floras source text into a list of tokens."""

from __future__ import annotations

from floras.errors import FlorasSyntaxError
from floras.tokens import KEYWORDS, Token, TokenKind

_IDENT_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_IDENT_CONT = _IDENT_START + "0123456789"
_DIGITS = "0123456789"


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
            if ch == "\n":
                self._advance()
                continue
            if ch.isspace():
                self._advance()
                continue
            if ch in _IDENT_START:
                self._read_identifier()
            elif ch in _DIGITS:
                self._read_number()
            else:
                raise FlorasSyntaxError(self.line, f"unexpected character {ch!r}")
        self.tokens.append(Token(TokenKind.EOF, "", self.line, self.col))
        return self.tokens

    def _read_identifier(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
        while not self._at_end() and self._peek() in _IDENT_CONT:
            self._advance()
        lexeme = self.src[start_pos : self.pos]

        if lexeme == "shion":
            # Line comment: consume to end-of-line. The `shion` keyword itself
            # is not emitted as a token.
            while not self._at_end() and self._peek() != "\n":
                self._advance()
            return

        if lexeme == "bara_kuchi":
            self._read_string(start_line, start_col)
            return

        kind = KEYWORDS.get(lexeme, TokenKind.IDENT)
        self.tokens.append(Token(kind, lexeme, start_line, start_col))

    def _read_string(self, start_line: int, start_col: int) -> None:
        # Skip exactly one whitespace separator after `bara_kuchi` if present.
        if not self._at_end() and self._peek().isspace() and self._peek() != "\n":
            self._advance()

        buf: list[str] = []
        terminator = "bara_tojiru"
        while True:
            if self._at_end():
                raise FlorasSyntaxError(
                    start_line,
                    "unterminated string literal: missing 'bara_tojiru'",
                )

            # Look ahead for the terminator at a word boundary.
            if self._peek() == "b" and self._matches_word_at(self.pos, terminator):
                break

            ch = self._peek()
            buf.append(ch)
            self._advance()

        # Strip exactly one trailing whitespace separator if present.
        if buf and buf[-1].isspace() and buf[-1] != "\n":
            buf.pop()

        # Consume the terminator keyword.
        for _ in range(len(terminator)):
            self._advance()

        self.tokens.append(
            Token(
                TokenKind.STRING,
                "bara_kuchi ... bara_tojiru",
                start_line,
                start_col,
                value="".join(buf),
            )
        )

    def _matches_word_at(self, pos: int, word: str) -> bool:
        end = pos + len(word)
        if end > len(self.src):
            return False
        if self.src[pos:end] != word:
            return False
        # Word boundary: next char must not be an identifier-continuation char.
        if end < len(self.src) and self.src[end] in _IDENT_CONT:
            return False
        # Left boundary: previous char (if any in current token start) must not
        # extend the word. The lexer enters this method only at a fresh char so
        # this is satisfied by construction.
        return True

    def _read_number(self) -> None:
        start_line, start_col = self.line, self.col
        start_pos = self.pos
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
            self._advance()  # consume '.'
            while not self._at_end() and self._peek() in _DIGITS:
                self._advance()
        lexeme = self.src[start_pos : self.pos]
        value: float | int = float(lexeme) if is_float else int(lexeme)
        self.tokens.append(
            Token(TokenKind.NUMBER, lexeme, start_line, start_col, value=value)
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
    """Convert source text into a list of tokens (terminated by an EOF token)."""
    return _Lexer(source).tokenize()
