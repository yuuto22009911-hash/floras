"""Recursive-descent parser for the Floras Bloom DSL (v0.1.0)."""

from __future__ import annotations

from floras.ast_nodes import (
    AngleValue,
    BloomDecl,
    BoolValue,
    BouquetDecl,
    ColorValue,
    Coord,
    ExportDecl,
    HexColor,
    IdentValue,
    NumberValue,
    OklchColor,
    PaletteDecl,
    PaletteRef,
    PercentValue,
    Placement,
    Program,
    Range,
    StringValue,
    StrokeSpec,
    Value,
)
from floras.errors import FlorasSyntaxError
from floras.tokens import Token, TokenKind

# Properties whose value is a colour (and therefore must be parsed via the
# `color_value` non-terminal rather than the generic `value`).
_COLOR_PROPERTIES: frozenset[str] = frozenset(
    {"color", "stamen-color", "stem-color", "background"}
)

# Properties whose value is `<color> width <number>` shorthand.
_STROKE_PROPERTIES: frozenset[str] = frozenset({"stroke"})


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ---------------------------------------------------------------- entry

    def parse_program(self) -> Program:
        program = Program()
        while not self._check(TokenKind.EOF):
            tok = self._peek()
            if tok.kind == TokenKind.PALETTE:
                program.palettes.append(self._parse_palette())
            elif tok.kind == TokenKind.BLOOM:
                program.blooms.append(self._parse_bloom())
            elif tok.kind == TokenKind.BOUQUET:
                program.bouquets.append(self._parse_bouquet())
            elif tok.kind == TokenKind.EXPORT:
                program.exports.append(self._parse_export())
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    f"expected top-level declaration "
                    f"(palette / bloom / bouquet / export), "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )
        return program

    # ------------------------------------------------------------ palette

    def _parse_palette(self) -> PaletteDecl:
        kw = self._consume(TokenKind.PALETTE)
        name = self._consume_ident("expected palette name").lexeme
        self._consume(TokenKind.LBRACE, "expected '{' after palette name")
        tokens: dict[str, ColorValue] = {}
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            tok_name = self._parse_token_name()
            color = self._parse_color_value()
            self._consume(TokenKind.SEMI, "expected ';' after palette entry")
            if tok_name in tokens:
                raise FlorasSyntaxError(
                    color.line,
                    f"duplicate palette token '{tok_name}' in palette '{name}'",
                )
            tokens[tok_name] = color
        self._consume(TokenKind.RBRACE, "expected '}' to close palette")
        return PaletteDecl(name=name, tokens=tokens, line=kw.line)

    def _parse_token_name(self) -> str:
        """Palette token names may be identifiers (`primary`) or integers (`500`)."""
        tok = self._peek()
        if tok.kind == TokenKind.IDENT:
            self._advance()
            return tok.lexeme
        if tok.kind == TokenKind.NUMBER:
            self._advance()
            assert isinstance(tok.value, float)
            return str(int(tok.value))
        raise FlorasSyntaxError(
            tok.line, f"expected palette token name, got '{tok.lexeme or tok.kind.value}'"
        )

    # -------------------------------------------------------------- bloom

    def _parse_bloom(self) -> BloomDecl:
        kw = self._consume(TokenKind.BLOOM)
        name = self._consume_ident("expected bloom name").lexeme
        self._consume(TokenKind.LBRACE, "expected '{' after bloom name")
        bloom = BloomDecl(name=name, line=kw.line)
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            self._parse_bloom_property(bloom)
        self._consume(TokenKind.RBRACE, "expected '}' to close bloom")
        return bloom

    def _parse_bloom_property(self, bloom: BloomDecl) -> None:
        key_tok = self._advance()
        key = key_tok.lexeme

        if key in bloom.properties:
            raise FlorasSyntaxError(
                key_tok.line, f"duplicate property '{key}' in bloom '{bloom.name}'"
            )

        if key in _STROKE_PROPERTIES:
            color = self._parse_color_value()
            self._consume(TokenKind.WIDTH, "expected 'width' after stroke colour")
            width_tok = self._consume_number("expected stroke width number")
            assert width_tok.value is not None
            bloom.properties[key] = StrokeSpec(
                color=color,
                width=float(width_tok.value),  # type: ignore[arg-type]
                line=key_tok.line,
            )
        elif key in _COLOR_PROPERTIES:
            bloom.properties[key] = self._parse_color_value()
        else:
            bloom.properties[key] = self._parse_value()

        self._consume(TokenKind.SEMI, "expected ';' after bloom property")

    # ------------------------------------------------------------- bouquet

    def _parse_bouquet(self) -> BouquetDecl:
        kw = self._consume(TokenKind.BOUQUET)
        name = self._consume_ident("expected bouquet name").lexeme
        self._consume(TokenKind.LBRACE, "expected '{' after bouquet name")

        # The first statement MUST be `canvas W x H;`.
        canvas_w, canvas_h = self._parse_canvas_decl()
        bouquet = BouquetDecl(
            name=name,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            line=kw.line,
        )

        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            tok = self._peek()
            if tok.kind == TokenKind.BACKGROUND:
                if bouquet.background is not None:
                    raise FlorasSyntaxError(
                        tok.line, "duplicate 'background' in bouquet"
                    )
                self._advance()
                bouquet.background = self._parse_color_value()
                self._consume(TokenKind.SEMI, "expected ';' after background")
            elif tok.kind == TokenKind.PLACE:
                bouquet.placements.append(self._parse_placement())
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    f"expected 'background' or 'place' inside bouquet, "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )

        self._consume(TokenKind.RBRACE, "expected '}' to close bouquet")
        return bouquet

    def _parse_canvas_decl(self) -> tuple[float, float]:
        self._consume(TokenKind.CANVAS, "bouquet must begin with 'canvas <W> x <H>;'")
        w_tok = self._consume_number("expected canvas width")
        # `1200 x 630` — the `x` is lexed as the X_KW reserved keyword token.
        self._consume(TokenKind.X_KW, "expected 'x' between canvas dimensions")
        h_tok = self._consume_number("expected canvas height")
        self._consume(TokenKind.SEMI, "expected ';' after canvas declaration")
        assert isinstance(w_tok.value, float) and isinstance(h_tok.value, float)
        return float(w_tok.value), float(h_tok.value)

    def _parse_placement(self) -> Placement:
        kw = self._consume(TokenKind.PLACE)
        target = self._consume_ident("expected bloom name after 'place'").lexeme
        self._consume(TokenKind.AT, "expected 'at' after place target")
        coord = self._parse_coord()

        overrides: dict[str, Value | StrokeSpec] = {}
        if self._check(TokenKind.LBRACE):
            self._advance()
            while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
                self._parse_placement_override(overrides)
            self._consume(TokenKind.RBRACE, "expected '}' to close place block")
        self._consume(TokenKind.SEMI, "expected ';' after place statement")
        return Placement(
            target=target, coord=coord, overrides=overrides, line=kw.line
        )

    def _parse_placement_override(
        self, overrides: dict[str, Value | StrokeSpec]
    ) -> None:
        key_tok = self._advance()
        key = key_tok.lexeme
        if key in overrides:
            raise FlorasSyntaxError(
                key_tok.line, f"duplicate placement override '{key}'"
            )
        if key == "stroke":
            color = self._parse_color_value()
            self._consume(TokenKind.WIDTH, "expected 'width' after stroke colour")
            width_tok = self._consume_number("expected stroke width number")
            assert width_tok.value is not None
            overrides[key] = StrokeSpec(
                color=color,
                width=float(width_tok.value),  # type: ignore[arg-type]
                line=key_tok.line,
            )
        elif key in {"color", "stamen-color", "stem-color"}:
            overrides[key] = self._parse_color_value()
        else:
            overrides[key] = self._parse_value()
        self._consume(TokenKind.SEMI, "expected ';' after placement override")

    def _parse_coord(self) -> Coord:
        tok = self._peek()
        if tok.kind == TokenKind.CENTER:
            self._advance()
            return Coord(is_center=True, line=tok.line)
        if tok.kind == TokenKind.LPAREN:
            self._advance()
            x_tok = self._consume_number("expected x coordinate")
            self._consume(TokenKind.COMMA, "expected ',' between coordinates")
            y_tok = self._consume_number("expected y coordinate")
            self._consume(TokenKind.RPAREN, "expected ')' to close coordinate")
            assert isinstance(x_tok.value, float) and isinstance(y_tok.value, float)
            return Coord(x=float(x_tok.value), y=float(y_tok.value), line=tok.line)
        raise FlorasSyntaxError(
            tok.line, f"expected 'center' or '(x, y)', got '{tok.lexeme or tok.kind.value}'"
        )

    # -------------------------------------------------------------- export

    def _parse_export(self) -> ExportDecl:
        kw = self._consume(TokenKind.EXPORT)
        target = self._consume_ident("expected export target name").lexeme
        self._consume(TokenKind.TO, "expected 'to' after export target")
        path_tok = self._consume(TokenKind.STRING, "expected output path string")
        self._consume(TokenKind.SEMI, "expected ';' after export")
        assert path_tok.value is not None
        return ExportDecl(target=target, path=str(path_tok.value), line=kw.line)

    # ------------------------------------------------------------ values

    def _parse_value(self) -> Value:
        tok = self._peek()
        if tok.kind == TokenKind.NUMBER:
            return self._parse_number_or_range()
        if tok.kind == TokenKind.PIXEL:
            self._advance()
            assert tok.value is not None
            return NumberValue(value=float(tok.value), line=tok.line)  # type: ignore[arg-type]
        if tok.kind == TokenKind.PERCENT:
            self._advance()
            assert tok.value is not None
            return PercentValue(value=float(tok.value), line=tok.line)  # type: ignore[arg-type]
        if tok.kind == TokenKind.DEG:
            self._advance()
            assert tok.value is not None
            return AngleValue(degrees=float(tok.value), line=tok.line)  # type: ignore[arg-type]
        if tok.kind == TokenKind.TURN:
            self._advance()
            assert tok.value is not None
            return AngleValue(degrees=float(tok.value) * 360.0, line=tok.line)  # type: ignore[arg-type]
        if tok.kind == TokenKind.HEX_COLOR:
            self._advance()
            return HexColor(hex=str(tok.value), line=tok.line)
        if tok.kind == TokenKind.OKLCH:
            return self._parse_oklch()
        if tok.kind == TokenKind.STRING:
            self._advance()
            return StringValue(value=str(tok.value), line=tok.line)
        if tok.kind == TokenKind.TRUE:
            self._advance()
            return BoolValue(value=True, line=tok.line)
        if tok.kind == TokenKind.FALSE:
            self._advance()
            return BoolValue(value=False, line=tok.line)
        if tok.kind == TokenKind.IDENT:
            # Could be a palette ref `brand.500` or a bare identifier.
            if (
                self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].kind == TokenKind.DOT
            ):
                return self._parse_palette_ref()
            self._advance()
            return IdentValue(name=tok.lexeme, line=tok.line)
        if tok.kind in (
            TokenKind.CENTER,
            TokenKind.AUTO,
            TokenKind.RANDOM,
            TokenKind.NONE_KW,
            TokenKind.SPIRAL,
            TokenKind.RING,
        ):
            self._advance()
            return IdentValue(name=tok.lexeme, line=tok.line)
        raise FlorasSyntaxError(
            tok.line, f"unexpected token in value position: '{tok.lexeme or tok.kind.value}'"
        )

    def _parse_number_or_range(self) -> Value:
        first = self._advance()
        assert first.value is not None
        first_value = float(first.value)  # type: ignore[arg-type]
        if self._check(TokenKind.DOTDOT):
            self._advance()
            tail = self._consume_number("expected upper bound after '..' in range")
            assert tail.value is not None
            return Range(
                min=first_value, max=float(tail.value), line=first.line  # type: ignore[arg-type]
            )
        return NumberValue(value=first_value, line=first.line)

    def _parse_color_value(self) -> ColorValue:
        tok = self._peek()
        if tok.kind == TokenKind.HEX_COLOR:
            self._advance()
            return HexColor(hex=str(tok.value), line=tok.line)
        if tok.kind == TokenKind.OKLCH:
            return self._parse_oklch()
        if tok.kind == TokenKind.IDENT:
            return self._parse_palette_ref()
        raise FlorasSyntaxError(
            tok.line,
            f"expected colour value (hex / oklch / palette-ref), "
            f"got '{tok.lexeme or tok.kind.value}'",
        )

    def _parse_oklch(self) -> OklchColor:
        kw = self._consume(TokenKind.OKLCH)
        self._consume(TokenKind.LPAREN, "expected '(' after 'oklch'")
        lightness = self._consume_number("expected lightness in oklch()")
        chroma = self._consume_number("expected chroma in oklch()")
        hue = self._consume_number("expected hue in oklch()")
        self._consume(TokenKind.RPAREN, "expected ')' to close oklch()")
        assert (
            lightness.value is not None
            and chroma.value is not None
            and hue.value is not None
        )
        return OklchColor(
            l=float(lightness.value),  # type: ignore[arg-type]
            c=float(chroma.value),  # type: ignore[arg-type]
            h=float(hue.value),  # type: ignore[arg-type]
            line=kw.line,
        )

    def _parse_palette_ref(self) -> PaletteRef:
        head = self._consume(TokenKind.IDENT, "expected palette name")
        self._consume(TokenKind.DOT, "expected '.' in palette reference")
        tok_name = self._parse_token_name()
        ref = PaletteRef(palette=head.lexeme, token=tok_name, line=head.line)
        if self._check(TokenKind.TINTED):
            self._advance()
            tint_palette_or_ref = self._consume_ident("expected tint palette name")
            tint_token: str
            if self._check(TokenKind.DOT):
                self._advance()
                tint_token = self._parse_token_name()
                tint_palette = tint_palette_or_ref.lexeme
            else:
                # Single-name tint refers to a token in the same palette as `ref`.
                tint_palette = ref.palette
                tint_token = tint_palette_or_ref.lexeme
            amount_tok = self._consume_number("expected tint amount (0..1)")
            assert amount_tok.value is not None
            ref = PaletteRef(
                palette=ref.palette,
                token=ref.token,
                tint_palette=tint_palette,
                tint_token=tint_token,
                tint_amount=float(amount_tok.value),  # type: ignore[arg-type]
                line=ref.line,
            )
        return ref

    # ----------------------------------------------------------- helpers

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != TokenKind.EOF:
            self.pos += 1
        return tok

    def _check(self, kind: TokenKind) -> bool:
        return self._peek().kind == kind

    def _consume(self, kind: TokenKind, message: str | None = None) -> Token:
        if self._check(kind):
            return self._advance()
        tok = self._peek()
        msg = (
            message
            if message is not None
            else f"expected {kind.value} but got '{tok.lexeme or tok.kind.value}'"
        )
        raise FlorasSyntaxError(tok.line, msg)

    def _consume_ident(self, message: str) -> Token:
        return self._consume(TokenKind.IDENT, message)

    def _consume_number(self, message: str) -> Token:
        if self._check(TokenKind.NUMBER):
            return self._advance()
        tok = self._peek()
        raise FlorasSyntaxError(tok.line, message)
