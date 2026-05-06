"""CLI entrypoint for Floras Bloom (`floras render`)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from floras import __version__
from floras.compose import compose
from floras.errors import FlorasError, FlorasInternalError
from floras.lexer import tokenize
from floras.parser import Parser
from floras.renderers.svg import render_svg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="floras",
        description="Floras Bloom — render flower-themed SVG/HTML/CSS from a .bloom DSL.",
    )
    parser.add_argument("--version", action="version", version=f"floras {__version__}")
    sub = parser.add_subparsers(dest="command")

    render_p = sub.add_parser("render", help="render a .bloom file to an SVG")
    render_p.add_argument("file", type=str, help="path to a .bloom source file")
    render_p.add_argument("--out", type=str, default=None, help="output SVG path (default: stdout)")
    render_p.add_argument("--entry", type=str, default=None, help="bloom name to render")
    render_p.add_argument(
        "--ast", action="store_true", help="emit the parsed AST as JSON instead of SVG"
    )

    args = parser.parse_args(argv)

    if args.command == "render":
        return _cmd_render(args.file, out=args.out, entry=args.entry, dump_ast=args.ast)

    parser.print_help()
    return 0


def _cmd_render(filepath: str, *, out: str | None, entry: str | None, dump_ast: bool) -> int:
    path = Path(filepath)
    if not path.is_file():
        sys.stderr.write(f"Floras Error: file not found: {filepath}\n")
        return 2

    source = path.read_text(encoding="utf-8")

    try:
        tokens = tokenize(source)
        program = Parser(tokens).parse_program()
        if dump_ast:
            sys.stdout.write(
                json.dumps(_ast_to_json(program), indent=2, ensure_ascii=False, default=str)
            )
            sys.stdout.write("\n")
            return 0
        scene = compose(program, entry=entry)
        svg = render_svg(scene)
    except FlorasError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        sys.stderr.write(f"{FlorasInternalError(0, f'unhandled host error: {exc}')}\n")
        return 1

    if out is None:
        sys.stdout.write(svg)
    else:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg, encoding="utf-8")
    return 0


def _ast_to_json(node: Any) -> Any:
    if is_dataclass(node) and not isinstance(node, type):
        out: dict[str, Any] = {"type": type(node).__name__}
        for k, v in asdict(node).items():
            out[k] = _ast_to_json(v)
        return out
    if isinstance(node, list):
        return [_ast_to_json(x) for x in node]
    if isinstance(node, tuple):
        return [_ast_to_json(x) for x in node]
    if isinstance(node, dict):
        return {k: _ast_to_json(v) for k, v in node.items()}
    return node


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
