"""Floras — a small interpreted language whose every syntactic element is a flower name."""

__version__ = "0.1.0"

from floras.errors import (
    FlorasArityError,
    FlorasError,
    FlorasInternalError,
    FlorasNameError,
    FlorasRuntimeError,
    FlorasSyntaxError,
    FlorasTypeError,
)

__all__ = [
    "FlorasArityError",
    "FlorasError",
    "FlorasInternalError",
    "FlorasNameError",
    "FlorasRuntimeError",
    "FlorasSyntaxError",
    "FlorasTypeError",
    "__version__",
    "run",
]


def run(source: str) -> str:
    """Lex, parse, and evaluate `source`. Returns captured stdout as a string.

    Designed for the future Web Playground (v1.0.0): single entry point that
    avoids touching the real stdout. v0.1.0 uses it for tests.
    """
    import io
    from contextlib import redirect_stdout

    from floras.evaluator import Evaluator
    from floras.lexer import tokenize
    from floras.parser import Parser

    tokens = tokenize(source)
    program = Parser(tokens).parse_program()
    buf = io.StringIO()
    with redirect_stdout(buf):
        Evaluator().evaluate(program)
    return buf.getvalue()
