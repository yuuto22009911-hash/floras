"""Error hierarchy for Floras Bloom. All errors carry a 1-origin source line."""

from __future__ import annotations


class FlorasError(Exception):
    kind: str = "Error"

    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        super().__init__(f"Floras {self.kind} at line {line}: {message}")


class FlorasSyntaxError(FlorasError):
    kind = "SyntaxError"


class FlorasNameError(FlorasError):
    kind = "NameError"


class FlorasValidationError(FlorasError):
    kind = "ValidationError"


class FlorasRuntimeError(FlorasError):
    kind = "RuntimeError"


class FlorasCLIError(FlorasError):
    kind = "CLIError"


class FlorasInternalError(FlorasError):
    kind = "InternalError"
