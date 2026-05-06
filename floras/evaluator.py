"""Tree-walking evaluator for Floras (v0.1.0)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
from floras.environment import Environment
from floras.errors import (
    FlorasArityError,
    FlorasInternalError,
    FlorasRuntimeError,
    FlorasTypeError,
)
from floras.tokens import TokenKind

# ---------------------------------------------------------------------------
# Runtime values
# ---------------------------------------------------------------------------


@dataclass
class Function:
    name: str
    params: list[str]
    body: list[Node]
    closure: Environment


@dataclass
class Builtin:
    name: str
    arity: int  # -1 = variadic
    fn: Callable[..., Any]


class _ReturnSignal(Exception):  # noqa: N818 — control-flow signal, not a public error
    """Internal signal used to unwind the call stack on `ran` (return)."""

    def __init__(self, value: Any) -> None:
        self.value = value


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class Evaluator:
    def __init__(self) -> None:
        self.globals = Environment()
        self._install_builtins()

    # ---- public API

    def evaluate(self, program: Program) -> None:
        for stmt in program.statements:
            self._exec(stmt, self.globals)

    # ---- builtins

    def _install_builtins(self) -> None:
        def _botan(*args: Any) -> Any:
            print(*[_format_value(a) for a in args])
            return None

        def _ayame(*_args: Any) -> Any:
            try:
                return input()
            except EOFError:
                return None

        self.globals.define("botan", Builtin("botan", -1, _botan))
        self.globals.define("ayame", Builtin("ayame", 0, _ayame))

    # ---- statements

    def _exec(self, node: Node, env: Environment) -> None:
        if isinstance(node, LetStmt):
            assert node.value is not None
            env.define(node.name, self._eval(node.value, env))
            return
        if isinstance(node, FnDecl):
            env.define(
                node.name,
                Function(name=node.name, params=node.params, body=node.body, closure=env),
            )
            return
        if isinstance(node, IfStmt):
            assert node.cond is not None
            if _truthy(self._eval(node.cond, env)):
                self._exec_block(node.then_branch, env)
            elif node.else_branch is not None:
                self._exec_block(node.else_branch, env)
            return
        if isinstance(node, WhileStmt):
            assert node.cond is not None
            while _truthy(self._eval(node.cond, env)):
                self._exec_block(node.body, env)
            return
        if isinstance(node, ReturnStmt):
            value: Any = None
            if node.value is not None:
                value = self._eval(node.value, env)
            raise _ReturnSignal(value)
        if isinstance(node, ExprStmt):
            assert node.expr is not None
            self._eval(node.expr, env)
            return
        raise FlorasInternalError(node.line, f"unhandled statement node: {type(node).__name__}")

    def _exec_block(self, stmts: list[Node], env: Environment) -> None:
        block_env = Environment(parent=env)
        for stmt in stmts:
            self._exec(stmt, block_env)

    # ---- expressions

    def _eval(self, node: Expr, env: Environment) -> Any:
        if isinstance(node, NumberLit):
            v = node.value
            return int(v) if v.is_integer() else v
        if isinstance(node, StringLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value
        if isinstance(node, NullLit):
            return None
        if isinstance(node, Identifier):
            return env.get(node.name, node.line)
        if isinstance(node, Assign):
            assert node.value is not None
            value = self._eval(node.value, env)
            env.assign(node.name, value, node.line)
            return value
        if isinstance(node, Unary):
            return self._eval_unary(node, env)
        if isinstance(node, Binary):
            return self._eval_binary(node, env)
        if isinstance(node, Call):
            return self._eval_call(node, env)
        raise FlorasInternalError(node.line, f"unhandled expression node: {type(node).__name__}")

    def _eval_unary(self, node: Unary, env: Environment) -> Any:
        assert node.operand is not None
        value = self._eval(node.operand, env)
        if node.op == TokenKind.KEITOU:  # unary minus
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise FlorasTypeError(
                    node.line, f"unary 'keitou' (-) expects a number, got {_type_name(value)}"
                )
            return -value
        if node.op == TokenKind.KESHI:  # logical not
            return not _truthy(value)
        raise FlorasInternalError(node.line, f"unhandled unary op: {node.op}")

    def _eval_binary(self, node: Binary, env: Environment) -> Any:
        assert node.left is not None and node.right is not None
        op = node.op

        # Short-circuit logical operators must not eagerly evaluate the RHS.
        if op == TokenKind.SUMIRE:  # &&
            left = self._eval(node.left, env)
            if not _truthy(left):
                return left
            return self._eval(node.right, env)
        if op == TokenKind.PANSY:  # ||
            left = self._eval(node.left, env)
            if _truthy(left):
                return left
            return self._eval(node.right, env)

        left = self._eval(node.left, env)
        right = self._eval(node.right, env)

        if op == TokenKind.MOMO:  # +
            if isinstance(left, str) or isinstance(right, str):
                return _to_string(left) + _to_string(right)
            _expect_numbers(node.line, "momo (+)", left, right)
            return _arith(left, right, lambda a, b: a + b)
        if op == TokenKind.KEITOU:  # -
            _expect_numbers(node.line, "keitou (-)", left, right)
            return _arith(left, right, lambda a, b: a - b)
        if op == TokenKind.MARIGOLD:  # *
            _expect_numbers(node.line, "marigold (*)", left, right)
            return _arith(left, right, lambda a, b: a * b)
        if op == TokenKind.SUZURAN:  # /
            _expect_numbers(node.line, "suzuran (/)", left, right)
            if right == 0:
                raise FlorasRuntimeError(node.line, "division by zero")
            return _arith(left, right, lambda a, b: a / b)
        if op == TokenKind.RENGE:  # %
            _expect_numbers(node.line, "renge (%)", left, right)
            if right == 0:
                raise FlorasRuntimeError(node.line, "modulo by zero")
            return _arith(left, right, lambda a, b: a % b)

        if op == TokenKind.WASURENAGUSA:  # ==
            return left == right
        if op == TokenKind.AZAMI:  # !=
            return left != right
        if op == TokenKind.FUKUJUSOU:  # <
            _expect_numbers(node.line, "fukujusou (<)", left, right)
            return left < right
        if op == TokenKind.TACHIAOI:  # >
            _expect_numbers(node.line, "tachiaoi (>)", left, right)
            return left > right
        if op == TokenKind.SUIREN:  # <=
            _expect_numbers(node.line, "suiren (<=)", left, right)
            return left <= right
        if op == TokenKind.SHOBU:  # >=
            _expect_numbers(node.line, "shobu (>=)", left, right)
            return left >= right

        raise FlorasInternalError(node.line, f"unhandled binary op: {op}")

    def _eval_call(self, node: Call, env: Environment) -> Any:
        assert node.callee is not None
        callee = self._eval(node.callee, env)
        args = [self._eval(a, env) for a in node.args]

        if isinstance(callee, Builtin):
            if callee.arity != -1 and len(args) != callee.arity:
                raise FlorasArityError(
                    node.line,
                    f"'{callee.name}' expects {callee.arity} args, got {len(args)}",
                )
            try:
                return callee.fn(*args)
            except FlorasRuntimeError:
                raise
            except Exception as exc:  # pragma: no cover - safety net for builtin failure
                raise FlorasInternalError(
                    node.line, f"builtin '{callee.name}' failed: {exc}"
                ) from exc

        if isinstance(callee, Function):
            if len(args) != len(callee.params):
                raise FlorasArityError(
                    node.line,
                    f"'{callee.name}' expects {len(callee.params)} args, got {len(args)}",
                )
            call_env = Environment(parent=callee.closure)
            for param, arg in zip(callee.params, args, strict=True):
                call_env.define(param, arg)
            try:
                for stmt in callee.body:
                    self._exec(stmt, call_env)
            except _ReturnSignal as ret:
                return ret.value
            return None

        if isinstance(node.callee, Identifier):
            raise FlorasTypeError(
                node.line, f"'{node.callee.name}' is not callable"
            )
        raise FlorasTypeError(node.line, "expression is not callable")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    return True


def _expect_numbers(line: int, label: str, left: Any, right: Any) -> None:
    if (
        not isinstance(left, (int, float))
        or isinstance(left, bool)
        or not isinstance(right, (int, float))
        or isinstance(right, bool)
    ):
        raise FlorasTypeError(
            line,
            f"{label} expects two numbers, got {_type_name(left)} and {_type_name(right)}",
        )


def _arith(left: Any, right: Any, op: Callable[[Any, Any], Any]) -> Any:
    result = op(left, right)
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result


def _type_name(value: Any) -> str:
    if value is None:
        return "tanpopo"
    if isinstance(value, bool):
        return "hasu/asagao"
    if isinstance(value, int) or isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Function):
        return "function"
    if isinstance(value, Builtin):
        return "builtin"
    return type(value).__name__


def _format_value(value: Any) -> str:
    if value is None:
        return "tanpopo"
    if isinstance(value, bool):
        return "hasu" if value else "asagao"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _to_string(value: Any) -> str:
    return _format_value(value)
