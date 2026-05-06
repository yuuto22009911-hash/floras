"""Interactive REPL for Floras (FR-07 / AC-06-*)."""

from __future__ import annotations

import sys

from floras.errors import FlorasError
from floras.evaluator import Evaluator
from floras.lexer import tokenize
from floras.parser import Parser

PROMPT = "floras> "


def run_repl() -> int:
    evaluator = Evaluator()
    sys.stdout.write("Floras REPL — Ctrl-D to exit.\n")
    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            sys.stdout.write("\n")
            return 0
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            continue

        if not line.strip():
            continue

        try:
            tokens = tokenize(line)
            program = Parser(tokens).parse_program()
            evaluator.evaluate(program)
        except FlorasError as exc:
            sys.stderr.write(f"{exc}\n")
        except Exception as exc:  # pragma: no cover - last-resort guard
            sys.stderr.write(f"Floras InternalError: {exc}\n")
