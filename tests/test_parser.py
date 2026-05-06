"""Parser tests — minimum coverage of each rule and the D-05 mixed-op rule."""

from __future__ import annotations

import pytest

from floras.ast_nodes import (
    Assign,
    Binary,
    Call,
    ExprStmt,
    FnDecl,
    Identifier,
    IfStmt,
    LetStmt,
    NumberLit,
    Program,
    ReturnStmt,
    StringLit,
    Unary,
    WhileStmt,
)
from floras.errors import FlorasSyntaxError
from floras.lexer import tokenize
from floras.parser import Parser
from floras.tokens import TokenKind


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse_program()


def test_let_statement() -> None:
    program = parse("sakura x tsuyukusa 1 nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, LetStmt)
    assert stmt.name == "x"
    assert isinstance(stmt.value, NumberLit)
    assert stmt.value.value == 1.0


def test_function_declaration_with_params() -> None:
    program = parse(
        "yuri add kobushi a kasumi b mokuren ajisai "
        "ran kobushi a momo b mokuren nadeshiko "
        "kikyou"
    )
    [stmt] = program.statements
    assert isinstance(stmt, FnDecl)
    assert stmt.name == "add"
    assert stmt.params == ["a", "b"]
    assert isinstance(stmt.body[0], ReturnStmt)


def test_if_else_chain() -> None:
    program = parse(
        "bara kobushi 1 mokuren ajisai kikyou "
        "tsubaki bara kobushi 2 mokuren ajisai kikyou "
        "tsubaki ajisai kikyou"
    )
    [stmt] = program.statements
    assert isinstance(stmt, IfStmt)
    assert stmt.else_branch is not None
    assert isinstance(stmt.else_branch[0], IfStmt)


def test_while_loop() -> None:
    program = parse("ume kobushi 1 mokuren ajisai kikyou")
    [stmt] = program.statements
    assert isinstance(stmt, WhileStmt)


def test_assignment_expression() -> None:
    program = parse("x tsuyukusa 5 nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Assign)
    assert stmt.expr.name == "x"


def test_same_operator_chain_is_left_associative() -> None:
    program = parse("1 momo 2 momo 3 nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    expr = stmt.expr
    assert isinstance(expr, Binary)
    # Left-associative: ((1+2)+3) → outer right is NumberLit(3), outer left is Binary.
    assert isinstance(expr.right, NumberLit) and expr.right.value == 3.0
    assert isinstance(expr.left, Binary)


def test_mixed_operators_without_parens_raise() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("1 momo 2 marigold 3 nadeshiko")


def test_grouping_allows_mixed_operators() -> None:
    program = parse("kobushi 1 momo 2 mokuren marigold 3 nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    expr = stmt.expr
    assert isinstance(expr, Binary)
    assert expr.op == TokenKind.MARIGOLD


def test_unary_minus_and_not() -> None:
    program = parse("keitou 5 nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Unary)
    assert stmt.expr.op == TokenKind.KEITOU


def test_function_call_with_args() -> None:
    program = parse("add kobushi 1 kasumi 2 mokuren nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Call)
    assert isinstance(stmt.expr.callee, Identifier)
    assert len(stmt.expr.args) == 2


def test_string_literal_as_expression() -> None:
    program = parse("bara_kuchi hi bara_tojiru nadeshiko")
    [stmt] = program.statements
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, StringLit)
    assert stmt.expr.value == "hi"


def test_missing_nadeshiko_is_error() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("sakura x tsuyukusa 1")


def test_unexpected_token_is_error() -> None:
    with pytest.raises(FlorasSyntaxError):
        parse("kasumi nadeshiko")
