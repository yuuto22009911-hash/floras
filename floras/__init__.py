"""Floras Bloom — a flower-themed declarative DSL that emits SVG / HTML / CSS."""

from __future__ import annotations

__version__ = "0.5.0"

from floras.errors import (
    FlorasCLIError,
    FlorasError,
    FlorasInternalError,
    FlorasNameError,
    FlorasRuntimeError,
    FlorasSyntaxError,
    FlorasValidationError,
)

__all__ = [
    "FlorasCLIError",
    "FlorasError",
    "FlorasInternalError",
    "FlorasNameError",
    "FlorasRuntimeError",
    "FlorasSyntaxError",
    "FlorasValidationError",
    "__version__",
    "render",
]


def render(source: str, *, entry: str | None = None) -> str:
    """Lex / parse / compose / render a `.bloom` source string into SVG.

    The returned string is a complete, standalone `<svg>...</svg>` document.
    """
    from floras.compose import compose
    from floras.lexer import tokenize
    from floras.parser import Parser
    from floras.renderers.svg import render_svg

    tokens = tokenize(source)
    program = Parser(tokens).parse_program()
    scene = compose(program, entry=entry)
    return render_svg(scene)
