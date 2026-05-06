"""AST node definitions for Floras (v0.1.0 Core)."""

from __future__ import annotations

from dataclasses import dataclass, field

from floras.tokens import TokenKind


@dataclass
class Node:
    line: int = 0


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------


@dataclass
class LetStmt(Node):
    name: str = ""
    value: Expr | None = None


@dataclass
class FnDecl(Node):
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Node] = field(default_factory=list)


@dataclass
class IfStmt(Node):
    cond: Expr | None = None
    then_branch: list[Node] = field(default_factory=list)
    else_branch: list[Node] | None = None


@dataclass
class WhileStmt(Node):
    cond: Expr | None = None
    body: list[Node] = field(default_factory=list)


@dataclass
class ReturnStmt(Node):
    value: Expr | None = None


@dataclass
class ExprStmt(Node):
    expr: Expr | None = None


@dataclass
class Program(Node):
    statements: list[Node] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


@dataclass
class Expr(Node):
    pass


@dataclass
class NumberLit(Expr):
    value: float = 0.0


@dataclass
class StringLit(Expr):
    value: str = ""


@dataclass
class BoolLit(Expr):
    value: bool = False


@dataclass
class NullLit(Expr):
    pass


@dataclass
class Identifier(Expr):
    name: str = ""


@dataclass
class Assign(Expr):
    name: str = ""
    value: Expr | None = None


@dataclass
class Binary(Expr):
    op: TokenKind = TokenKind.MOMO
    left: Expr | None = None
    right: Expr | None = None


@dataclass
class Unary(Expr):
    op: TokenKind = TokenKind.KEITOU
    operand: Expr | None = None


@dataclass
class Call(Expr):
    callee: Expr | None = None
    args: list[Expr] = field(default_factory=list)
