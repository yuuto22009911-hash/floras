"""Error hierarchy for Floras. All errors carry a 1-origin source line number."""

from __future__ import annotations


class FlorasError(Exception):
    """Base class for all errors raised by the Floras pipeline.

    The CLI layer is responsible for catching these and emitting them to stderr.
    """

    kind: str = "Error"

    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        super().__init__(f"Floras {self.kind} at line {line}: {message}")


class FlorasSyntaxError(FlorasError):
    kind = "SyntaxError"


class FlorasNameError(FlorasError):
    kind = "NameError"


class FlorasTypeError(FlorasError):
    kind = "TypeError"


class FlorasArityError(FlorasError):
    kind = "ArityError"


class FlorasRuntimeError(FlorasError):
    kind = "RuntimeError"


class FlorasInternalError(FlorasError):
    kind = "InternalError"
