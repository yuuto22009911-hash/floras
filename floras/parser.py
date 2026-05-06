"""Recursive-descent parser for the all-Japanese Floras Bloom DSL."""

from __future__ import annotations

from floras.ast_nodes import (
    AngleValue,
    AreaCanvas,
    AreaGrid,
    AreaRect,
    AreaRing,
    AreaSpec,
    BloomDecl,
    BoolValue,
    BouquetDecl,
    ColorValue,
    Coord,
    ExportDecl,
    HexColor,
    IdentValue,
    MotifDecl,
    NumberValue,
    OklchColor,
    PaletteDecl,
    PaletteRef,
    PercentValue,
    Placement,
    Program,
    Range,
    ScatterDecl,
    StringValue,
    StrokeSpec,
    Value,
)
from floras.errors import FlorasSyntaxError
from floras.tokens import Token, TokenKind

# Bloom property keys whose value is a colour (must use the colour-value rule).
_COLOR_PROPERTIES: frozenset[str] = frozenset(
    {"色", "雄蕊色", "茎色", "背景"}
)


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ---------------------------------------------------------------- entry

    def parse_program(self) -> Program:
        program = Program()
        while not self._check(TokenKind.EOF):
            tok = self._peek()
            if tok.kind == TokenKind.IROMIHON:
                program.palettes.append(self._parse_palette())
            elif tok.kind == TokenKind.HANA:
                program.blooms.append(self._parse_bloom())
            elif tok.kind == TokenKind.MOYOU:
                program.motifs.append(self._parse_motif())
            elif tok.kind == TokenKind.HANATABA:
                program.bouquets.append(self._parse_bouquet())
            elif tok.kind == TokenKind.KAKIDASHI:
                program.exports.append(self._parse_export())
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    "expected top-level declaration "
                    "(色見本 / 花 / 模様 / 花束 / 書出), "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )
        return program

    # ------------------------------------------------------------ palette

    def _parse_palette(self) -> PaletteDecl:
        kw = self._consume(TokenKind.IROMIHON)
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
        """Palette token names may be identifiers or integer literals."""
        tok = self._peek()
        if tok.kind == TokenKind.IDENT:
            self._advance()
            return tok.lexeme
        if tok.kind == TokenKind.NUMBER:
            self._advance()
            assert isinstance(tok.value, float)
            return str(int(tok.value))
        raise FlorasSyntaxError(
            tok.line,
            f"expected palette token name, got '{tok.lexeme or tok.kind.value}'",
        )

    # -------------------------------------------------------------- bloom

    def _parse_bloom(self) -> BloomDecl:
        kw = self._consume(TokenKind.HANA)
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
        if key == "輪郭":
            color = self._parse_color_value()
            self._consume(TokenKind.HABA, "expected '幅' after stroke colour")
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

    # ------------------------------------------------------------- motif

    def _parse_motif(self) -> MotifDecl:
        kw = self._consume(TokenKind.MOYOU)
        name = self._consume_ident("expected motif name").lexeme
        self._consume(TokenKind.LBRACE, "expected '{' after motif name")
        placements: list[Placement] = []
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            tok = self._peek()
            if tok.kind == TokenKind.OKU:
                placements.append(self._parse_placement())
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    "expected '置く' inside motif, "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )
        self._consume(TokenKind.RBRACE, "expected '}' to close motif")
        return MotifDecl(name=name, placements=placements, line=kw.line)

    # ------------------------------------------------------------- bouquet

    def _parse_bouquet(self) -> BouquetDecl:
        kw = self._consume(TokenKind.HANATABA)
        name = self._consume_ident("expected bouquet name").lexeme
        self._consume(TokenKind.LBRACE, "expected '{' after bouquet name")

        canvas_w, canvas_h = self._parse_canvas_decl()
        bouquet = BouquetDecl(
            name=name,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            line=kw.line,
        )
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            tok = self._peek()
            if tok.kind == TokenKind.HAIKEI:
                if bouquet.background is not None:
                    raise FlorasSyntaxError(
                        tok.line, "duplicate '背景' in bouquet"
                    )
                self._advance()
                bouquet.background = self._parse_color_value()
                self._consume(TokenKind.SEMI, "expected ';' after 背景")
            elif tok.kind == TokenKind.OKU:
                bouquet.placements.append(self._parse_placement())
            elif tok.kind == TokenKind.CHIRASU:
                bouquet.scatters.append(self._parse_scatter())
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    "expected '背景' / '置く' / '散らす' inside bouquet, "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )

        self._consume(TokenKind.RBRACE, "expected '}' to close bouquet")
        return bouquet

    def _parse_canvas_decl(self) -> tuple[float, float]:
        self._consume(
            TokenKind.GAFU, "bouquet must begin with '画布 <W> × <H>;'"
        )
        w_tok = self._consume_number("expected canvas width")
        self._consume(TokenKind.TIMES, "expected '×' between canvas dimensions")
        h_tok = self._consume_number("expected canvas height")
        self._consume(TokenKind.SEMI, "expected ';' after canvas declaration")
        assert isinstance(w_tok.value, float) and isinstance(h_tok.value, float)
        return float(w_tok.value), float(h_tok.value)

    def _parse_placement(self) -> Placement:
        kw = self._consume(TokenKind.OKU)
        target = self._consume_ident("expected bloom name after '置く'").lexeme
        self._consume(TokenKind.NI, "expected 'に' after place target")
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
        if key == "輪郭":
            color = self._parse_color_value()
            self._consume(TokenKind.HABA, "expected '幅' after stroke colour")
            width_tok = self._consume_number("expected stroke width number")
            assert width_tok.value is not None
            overrides[key] = StrokeSpec(
                color=color,
                width=float(width_tok.value),  # type: ignore[arg-type]
                line=key_tok.line,
            )
        elif key in _COLOR_PROPERTIES:
            overrides[key] = self._parse_color_value()
        else:
            overrides[key] = self._parse_value()
        self._consume(TokenKind.SEMI, "expected ';' after placement override")

    def _parse_coord(self) -> Coord:
        tok = self._peek()
        if tok.kind == TokenKind.CHUUOU:
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
            tok.line,
            "expected '中央' or '(x, y)', "
            f"got '{tok.lexeme or tok.kind.value}'",
        )

    # ------------------------------------------------------------- scatter

    def _parse_scatter(self) -> ScatterDecl:
        kw = self._consume(TokenKind.CHIRASU)
        # The block name is optional; it documents the scatter but isn't
        # otherwise used. Allow either `散らす 名前 { ... }` or `散らす { ... }`.
        if self._check(TokenKind.IDENT):
            self._advance()
        self._consume(TokenKind.LBRACE, "expected '{' to open scatter block")
        seen: dict[str, bool] = {}
        source: str | None = None
        count: int | str | None = None
        area: AreaSpec | None = None
        seed: int | None = None
        size: Value | None = None
        rotation: Value | None = None
        color: ColorValue | None = None
        while not self._check(TokenKind.RBRACE) and not self._check(TokenKind.EOF):
            tok = self._peek()
            key = tok.lexeme
            if key in seen:
                raise FlorasSyntaxError(
                    tok.line, f"duplicate scatter property '{key}'"
                )
            if tok.kind == TokenKind.MOTO:
                self._advance()
                source = self._consume_ident(
                    "expected bloom name after '元'"
                ).lexeme
            elif tok.kind == TokenKind.KAZU:
                self._advance()
                if self._check(TokenKind.JIDOU):
                    self._advance()
                    count = "自動"
                else:
                    n = self._consume_number("expected scatter count")
                    assert isinstance(n.value, float)
                    count = int(n.value)
            elif tok.kind == TokenKind.RYOUIKI:
                self._advance()
                area = self._parse_area_spec()
            elif tok.kind == TokenKind.TANE:
                self._advance()
                n = self._consume_number("expected seed value")
                assert isinstance(n.value, float)
                seed = int(n.value)
            elif tok.kind == TokenKind.OOKISA:
                self._advance()
                size = self._parse_value()
            elif tok.kind == TokenKind.KAITEN:
                self._advance()
                rotation = self._parse_value()
            elif tok.kind == TokenKind.IRO:
                self._advance()
                color = self._parse_color_value()
            else:
                raise FlorasSyntaxError(
                    tok.line,
                    "expected '元' / '数' / '領域' / '種' / '大きさ' / '回転' / '色', "
                    f"got '{tok.lexeme or tok.kind.value}'",
                )
            seen[key] = True
            self._consume(TokenKind.SEMI, "expected ';' after scatter property")
        self._consume(TokenKind.RBRACE, "expected '}' to close scatter")

        if source is None:
            raise FlorasSyntaxError(kw.line, "scatter requires '元 <bloom>;'")
        if count is None:
            raise FlorasSyntaxError(kw.line, "scatter requires '数 <count>;'")
        if area is None:
            raise FlorasSyntaxError(kw.line, "scatter requires '領域 <area>;'")
        if seed is None:
            # Determinism: every scatter must declare an explicit seed.
            raise FlorasSyntaxError(
                kw.line, "scatter requires '種 <integer>;' for determinism"
            )
        return ScatterDecl(
            source=source,
            count=count,
            area=area,
            seed=seed,
            size=size,
            rotation=rotation,
            color=color,
            line=kw.line,
        )

    def _parse_area_spec(self) -> AreaSpec:
        tok = self._peek()
        if tok.kind == TokenKind.GAFU:
            self._advance()
            return AreaCanvas()
        if tok.kind == TokenKind.WA:
            self._advance()
            self._consume(TokenKind.CHUUOU, "expected '中央' for ring area")
            self._consume(TokenKind.LPAREN, "expected '(' for ring centre")
            cx = self._consume_number("expected ring centre x")
            self._consume(TokenKind.COMMA, "expected ','")
            cy = self._consume_number("expected ring centre y")
            self._consume(TokenKind.RPAREN, "expected ')'")
            self._consume(TokenKind.UCHI, "expected '内' (inner radius)")
            inner = self._consume_number("expected inner radius")
            self._consume(TokenKind.SOTO, "expected '外' (outer radius)")
            outer = self._consume_number("expected outer radius")
            assert isinstance(cx.value, float)
            assert isinstance(cy.value, float)
            assert isinstance(inner.value, float)
            assert isinstance(outer.value, float)
            return AreaRing(
                center_x=float(cx.value),
                center_y=float(cy.value),
                inner=float(inner.value),
                outer=float(outer.value),
            )
        if tok.kind == TokenKind.KUKEI:
            self._advance()
            self._consume(TokenKind.LPAREN, "expected '(' for rect")
            x1 = self._consume_number("expected x1")
            self._consume(TokenKind.COMMA, "expected ','")
            y1 = self._consume_number("expected y1")
            self._consume(TokenKind.RPAREN, "expected ')'")
            self._consume(TokenKind.HE, "expected 'へ' between rect corners")
            self._consume(TokenKind.LPAREN, "expected '(' for rect")
            x2 = self._consume_number("expected x2")
            self._consume(TokenKind.COMMA, "expected ','")
            y2 = self._consume_number("expected y2")
            self._consume(TokenKind.RPAREN, "expected ')'")
            assert isinstance(x1.value, float)
            assert isinstance(y1.value, float)
            assert isinstance(x2.value, float)
            assert isinstance(y2.value, float)
            return AreaRect(
                x1=float(x1.value),
                y1=float(y1.value),
                x2=float(x2.value),
                y2=float(y2.value),
            )
        if tok.kind == TokenKind.KOUSHI:
            self._advance()
            self._consume(TokenKind.RETSU, "expected '列' (cols)")
            cols = self._consume_number("expected cols count")
            self._consume(TokenKind.GYOU, "expected '行' (rows)")
            rows = self._consume_number("expected rows count")
            assert isinstance(cols.value, float)
            assert isinstance(rows.value, float)
            return AreaGrid(cols=int(cols.value), rows=int(rows.value))
        raise FlorasSyntaxError(
            tok.line,
            "expected area spec ('画布' / '輪 中央 ...' / '矩形 ...' / '格子 ...'), "
            f"got '{tok.lexeme or tok.kind.value}'",
        )

    # -------------------------------------------------------------- export

    def _parse_export(self) -> ExportDecl:
        kw = self._consume(TokenKind.KAKIDASHI)
        target = self._consume_ident("expected export target name").lexeme
        self._consume(TokenKind.HE, "expected 'へ' after export target")
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
        if tok.kind == TokenKind.CHIKAKU_IRO:
            return self._parse_oklch()
        if tok.kind == TokenKind.STRING:
            self._advance()
            return StringValue(value=str(tok.value), line=tok.line)
        if tok.kind == TokenKind.SHIN:
            self._advance()
            return BoolValue(value=True, line=tok.line)
        if tok.kind == TokenKind.GI:
            self._advance()
            return BoolValue(value=False, line=tok.line)
        if tok.kind == TokenKind.IDENT:
            if (
                self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].kind == TokenKind.DOT
            ):
                return self._parse_palette_ref()
            self._advance()
            return IdentValue(name=tok.lexeme, line=tok.line)
        if tok.kind in (
            TokenKind.CHUUOU,
            TokenKind.JIDOU,
            TokenKind.RANSUU,
            TokenKind.MU,
            TokenKind.RASEN,
            TokenKind.WA,
        ):
            self._advance()
            return IdentValue(name=tok.lexeme, line=tok.line)
        raise FlorasSyntaxError(
            tok.line,
            f"unexpected token in value position: '{tok.lexeme or tok.kind.value}'",
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
        if tok.kind == TokenKind.CHIKAKU_IRO:
            return self._parse_oklch()
        if tok.kind == TokenKind.IDENT:
            return self._parse_palette_ref()
        raise FlorasSyntaxError(
            tok.line,
            "expected colour value (知覚色(...) or palette-ref), "
            f"got '{tok.lexeme or tok.kind.value}'",
        )

    def _parse_oklch(self) -> OklchColor:
        kw = self._consume(TokenKind.CHIKAKU_IRO)
        self._consume(TokenKind.LPAREN, "expected '(' after '知覚色'")
        lightness = self._consume_number("expected lightness in 知覚色")
        chroma = self._consume_number("expected chroma in 知覚色")
        hue = self._consume_number("expected hue in 知覚色")
        self._consume(TokenKind.RPAREN, "expected ')' to close 知覚色")
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
        if self._check(TokenKind.MAZE):
            self._advance()
            tint_palette_or_ref = self._consume_ident("expected tint palette name")
            tint_token: str
            if self._check(TokenKind.DOT):
                self._advance()
                tint_token = self._parse_token_name()
                tint_palette = tint_palette_or_ref.lexeme
            else:
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


# Re-export HexColor so the import remains usable without refactoring callers.
__all__ = ["Parser", "HexColor"]
