"""Lexical scope chain for the Floras evaluator."""

from __future__ import annotations

from typing import Any

from floras.errors import FlorasNameError


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self._values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self._values[name] = value

    def get(self, name: str, line: int) -> Any:
        if name in self._values:
            return self._values[name]
        if self.parent is not None:
            return self.parent.get(name, line)
        raise FlorasNameError(line, f"'{name}' is not defined")

    def assign(self, name: str, value: Any, line: int) -> None:
        if name in self._values:
            self._values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value, line)
            return
        raise FlorasNameError(line, f"'{name}' is not defined")
