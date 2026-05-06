"""Palette → CSS / Tailwind v4 / JSON exporters.

Each renderer converts the program's `色見本` declarations into a deployable
artefact for a frontend codebase. Palette and token names are emitted as-is,
so the generated CSS variables look like ``--春-桜色`` — modern browsers
support non-ASCII identifiers in custom properties.
"""

from __future__ import annotations

import json

from floras.ast_nodes import PaletteDecl
from floras.compose.resolver import build_palette_table


def render_css(palettes: list[PaletteDecl]) -> str:
    """Emit `:root { --<palette>-<token>: <hex>; }` block."""
    table = build_palette_table(_index(palettes))
    lines: list[str] = [
        "/* Floras Bloom palette — auto-generated, do not edit */",
        ":root {",
    ]
    for pal_name, tokens in table.items():
        for tok_name, hex_color in tokens.items():
            lines.append(f"  --{pal_name}-{tok_name}: {hex_color.hex};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_tailwind(palettes: list[PaletteDecl]) -> str:
    """Emit Tailwind v4 `@theme { --color-<palette>-<token>: <hex>; }` block."""
    table = build_palette_table(_index(palettes))
    lines: list[str] = [
        "/* Floras Bloom palette — Tailwind v4 @theme */",
        "@theme {",
    ]
    for pal_name, tokens in table.items():
        for tok_name, hex_color in tokens.items():
            lines.append(f"  --color-{pal_name}-{tok_name}: {hex_color.hex};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_json(palettes: list[PaletteDecl]) -> str:
    """Emit a nested JSON object: `{ palette: { token: hex } }`."""
    table = build_palette_table(_index(palettes))
    nested: dict[str, dict[str, str]] = {
        pal_name: {tok: hex_color.hex for tok, hex_color in tokens.items()}
        for pal_name, tokens in table.items()
    }
    return json.dumps(nested, ensure_ascii=False, indent=2) + "\n"


def _index(palettes: list[PaletteDecl]) -> dict[str, PaletteDecl]:
    return {p.name: p for p in palettes}
