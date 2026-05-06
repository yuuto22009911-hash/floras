"""Command-line entrypoint for Floras (`floras run` / `floras repl`)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from floras import __version__
from floras.ast_nodes import Program
from floras.errors import FlorasError, FlorasInternalError
from floras.evaluator import Evaluator
from floras.lexer import tokenize
from floras.parser import Parser
from floras.repl import run_repl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="floras",
        description="Floras — every syntactic element is a flower name.",
    )
    parser.add_argument("--version", action="version", version=f"floras {__version__}")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="run a .floras script")
    run_p.add_argument("file", type=str, help="path to a .floras file")
    run_p.add_argument(
        "--ast",
        action="store_true",
        help="dump the AST as JSON instead of executing",
    )
    run_p.add_argument(
        "--no-poesy",
        action="store_true",
        help="reserved for v0.2.0 — currently a no-op",
    )

    repl_p = sub.add_parser("repl", help="start the interactive REPL")
    repl_p.add_argument(
        "--no-poesy",
        action="store_true",
        help="reserved for v0.2.0 — currently a no-op",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        return _cmd_run(args.file, dump_ast=args.ast)
    if args.command == "repl":
        return run_repl() or 0

    parser.print_help()
    return 0


def _cmd_run(filepath: str, *, dump_ast: bool) -> int:
    path = Path(filepath)
    if not path.is_file():
        sys.stderr.write(f"Floras Error: file not found: {filepath}\n")
        return 2

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"Floras Error: cannot read {filepath}: {exc}\n")
        return 2

    try:
        tokens = tokenize(source)
        program = Parser(tokens).parse_program()
        if dump_ast:
            sys.stdout.write(json.dumps(_ast_to_json(program), indent=2, ensure_ascii=False))
            sys.stdout.write("\n")
            return 0
        Evaluator().evaluate(program)
    except FlorasError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except RecursionError:
        sys.stderr.write("Floras RuntimeError: maximum recursion depth exceeded\n")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        wrapped = FlorasInternalError(0, f"unhandled host error: {exc}")
        sys.stderr.write(f"{wrapped}\n")
        return 1
    return 0


def _ast_to_json(node: Any) -> Any:
    if is_dataclass(node) and not isinstance(node, type):
        out: dict[str, Any] = {"type": type(node).__name__}
        for k, v in asdict(node).items():
            out[k] = _ast_to_json(v)
        return out
    if isinstance(node, list):
        return [_ast_to_json(x) for x in node]
    if isinstance(node, dict):
        return {k: _ast_to_json(v) for k, v in node.items()}
    return node


# Ensure `floras` resolves Program correctly during pytest collection (mypy hint).
_ = Program  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
