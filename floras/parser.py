"""Recursive-descent parser for Floras (v0.1.0 Core, EBNF per design.md)."""

from __future__ import annotations

from floras.ast_nodes import (
    Assign,
    Binary,
    BoolLit,
    Call,
    Expr,
    ExprStmt,
    FnDecl,
    Identifier,
    IfStmt,
    LetStmt,
    Node,
    NullLit,
    NumberLit,
    Program,
    ReturnStmt,
    StringLit,
    Unary,
    WhileStmt,
)
from floras.errors import FlorasSyntaxError
from floras.tokens import BINARY_OPS, UNARY_OPS, Token, TokenKind


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------------ entry

    def parse_program(self) -> Program:
        statements: list[Node] = []
        while not self._check(TokenKind.EOF):
            statements.append(self._parse_statement())
        return Program(line=1, statements=statements)

    # --------------------------------------------------------------- statements

    def _parse_statement(self) -> Node:
        kind = self._peek().kind
        if kind == TokenKind.SAKURA:
            return self._parse_let()
        if kind == TokenKind.YURI:
            return self._parse_fn_decl()
        if kind == TokenKind.BARA:
            return self._parse_if()
        if kind == TokenKind.UME:
            return self._parse_while()
        if kind == TokenKind.RAN:
            return self._parse_return()
        return self._parse_expr_stmt()

    def _parse_let(self) -> LetStmt:
        kw = self._consume(TokenKind.SAKURA)
        name_tok = self._consume(TokenKind.IDENT, "expected variable name after 'sakura'")
        self._consume(TokenKind.TSUYUKUSA, "expected 'tsuyukusa' (=) in let")
        value = self._parse_expression()
        self._consume(TokenKind.NADESHIKO, "expected 'nadeshiko' (;) at end of statement")
        return LetStmt(line=kw.line, name=name_tok.lexeme, value=value)

    def _parse_fn_decl(self) -> FnDecl:
        kw = self._consume(TokenKind.YURI)
        name_tok = self._consume(TokenKind.IDENT, "expected function name after 'yuri'")
        self._consume(TokenKind.KOBUSHI, "expected '(' (kobushi) after function name")
        params: list[str] = []
        if not self._check(TokenKind.MOKUREN):
            params.append(self._consume(TokenKind.IDENT, "expected parameter name").lexeme)
            while self._match(TokenKind.KASUMI):
                params.append(self._consume(TokenKind.IDENT, "expected parameter name").lexeme)
        self._consume(TokenKind.MOKUREN, "expected ')' (mokuren) after parameters")
        body = self._parse_block()
        return FnDecl(line=kw.line, name=name_tok.lexeme, params=params, body=body)

    def _parse_if(self) -> IfStmt:
        kw = self._consume(TokenKind.BARA)
        self._consume(TokenKind.KOBUSHI, "expected '(' (kobushi) after 'bara'")
        cond = self._parse_expression()
        self._consume(TokenKind.MOKUREN, "expected ')' (mokuren) after if condition")
        then_branch = self._parse_block()
        else_branch: list[Node] | None = None
        if self._match(TokenKind.TSUBAKI):
            if self._check(TokenKind.BARA):
                else_branch = [self._parse_if()]
            else:
                else_branch = self._parse_block()
        return IfStmt(line=kw.line, cond=cond, then_branch=then_branch, else_branch=else_branch)

    def _parse_while(self) -> WhileStmt:
        kw = self._consume(TokenKind.UME)
        self._consume(TokenKind.KOBUSHI, "expected '(' (kobushi) after 'ume'")
        cond = self._parse_expression()
        self._consume(TokenKind.MOKUREN, "expected ')' (mokuren) after while condition")
        body = self._parse_block()
        return WhileStmt(line=kw.line, cond=cond, body=body)

    def _parse_return(self) -> ReturnStmt:
        kw = self._consume(TokenKind.RAN)
        value: Expr | None = None
        if not self._check(TokenKind.NADESHIKO):
            value = self._parse_expression()
        self._consume(TokenKind.NADESHIKO, "expected 'nadeshiko' (;) at end of return")
        return ReturnStmt(line=kw.line, value=value)

    def _parse_expr_stmt(self) -> ExprStmt:
        line = self._peek().line
        expr = self._parse_expression()
        self._consume(TokenKind.NADESHIKO, "expected 'nadeshiko' (;) at end of statement")
        return ExprStmt(line=line, expr=expr)

    def _parse_block(self) -> list[Node]:
        self._consume(TokenKind.AJISAI, "expected '{' (ajisai) at start of block")
        stmts: list[Node] = []
        while not self._check(TokenKind.KIKYOU) and not self._check(TokenKind.EOF):
            stmts.append(self._parse_statement())
        self._consume(TokenKind.KIKYOU, "expected '}' (kikyou) at end of block")
        return stmts

    # -------------------------------------------------------------- expressions

    def _parse_expression(self) -> Expr:
        # Assignment: IDENT 'tsuyukusa' expression — single right-recursive form
        # that we detect by lookahead. Otherwise fall through to binary.
        if (
            self._check(TokenKind.IDENT)
            and self._check_at(self.pos + 1, TokenKind.TSUYUKUSA)
        ):
            name_tok = self._advance()
            self._advance()  # consume tsuyukusa
            value = self._parse_expression()
            return Assign(line=name_tok.line, name=name_tok.lexeme, value=value)
        return self._parse_binary()

    def _parse_binary(self) -> Expr:
        left = self._parse_unary()
        if not self._is_binop():
            return left
        op_tok = self._peek()
        op = op_tok.kind
        operands: list[Expr] = [left]
        while self._is_binop():
            cur = self._peek().kind
            if cur != op:
                # D-05: mixed operators of different kinds require parenthesisation.
                raise FlorasSyntaxError(
                    self._peek().line,
                    "mixed operators are not allowed; wrap with 'kobushi ... mokuren' "
                    "(operator priority is intentionally absent — see ADR-13)",
                )
            self._advance()
            operands.append(self._parse_unary())

        # Left-associative fold.
        result: Expr = operands[0]
        for right in operands[1:]:
            result = Binary(line=op_tok.line, op=op, left=result, right=right)
        return result

    def _parse_unary(self) -> Expr:
        if self._peek().kind in UNARY_OPS:
            op_tok = self._advance()
            operand = self._parse_unary()
            return Unary(line=op_tok.line, op=op_tok.kind, operand=operand)
        return self._parse_call()

    def _parse_call(self) -> Expr:
        expr = self._parse_primary()
        while self._match(TokenKind.KOBUSHI):
            args: list[Expr] = []
            if not self._check(TokenKind.MOKUREN):
                args.append(self._parse_expression())
                while self._match(TokenKind.KASUMI):
                    args.append(self._parse_expression())
            self._consume(TokenKind.MOKUREN, "expected ')' (mokuren) after call arguments")
            expr = Call(line=expr.line, callee=expr, args=args)
        return expr

    def _parse_primary(self) -> Expr:
        tok = self._peek()
        if tok.kind == TokenKind.NUMBER:
            self._advance()
            assert tok.value is not None
            return NumberLit(line=tok.line, value=float(tok.value))  # type: ignore[arg-type]
        if tok.kind == TokenKind.STRING:
            self._advance()
            return StringLit(line=tok.line, value=str(tok.value))
        if tok.kind == TokenKind.HASU:
            self._advance()
            return BoolLit(line=tok.line, value=True)
        if tok.kind == TokenKind.ASAGAO:
            self._advance()
            return BoolLit(line=tok.line, value=False)
        if tok.kind == TokenKind.TANPOPO:
            self._advance()
            return NullLit(line=tok.line)
        if tok.kind in (TokenKind.IDENT, TokenKind.BOTAN, TokenKind.AYAME):
            # Builtin functions (botan/ayame) are reserved keywords (FR-10) but
            # they appear in expression position as ordinary callables; the
            # Environment binds them to native implementations.
            self._advance()
            return Identifier(line=tok.line, name=tok.lexeme)
        if tok.kind == TokenKind.KOBUSHI:
            self._advance()
            inner = self._parse_expression()
            self._consume(
                TokenKind.MOKUREN, "expected ')' (mokuren) after parenthesised expression"
            )
            return inner
        raise FlorasSyntaxError(tok.line, f"unexpected token '{tok.lexeme or tok.kind.value}'")

    # ------------------------------------------------------------------ helpers

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != TokenKind.EOF:
            self.pos += 1
        return tok

    def _check(self, kind: TokenKind) -> bool:
        return self._peek().kind == kind

    def _check_at(self, idx: int, kind: TokenKind) -> bool:
        if idx >= len(self.tokens):
            return False
        return self.tokens[idx].kind == kind

    def _match(self, kind: TokenKind) -> bool:
        if self._check(kind):
            self._advance()
            return True
        return False

    def _consume(self, kind: TokenKind, message: str | None = None) -> Token:
        if self._check(kind):
            return self._advance()
        tok = self._peek()
        msg = message or f"expected {kind.value} but got '{tok.lexeme or tok.kind.value}'"
        raise FlorasSyntaxError(tok.line, msg)

    def _is_binop(self) -> bool:
        return self._peek().kind in BINARY_OPS
