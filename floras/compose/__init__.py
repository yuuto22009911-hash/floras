"""Compose pipeline: AST → resolved SceneGraph."""

from __future__ import annotations

from floras.ast_nodes import BloomDecl, PaletteDecl, Program
from floras.compose.resolver import build_palette_table, resolve_bloom
from floras.compose.scene import Scene
from floras.errors import FlorasNameError, FlorasValidationError


def compose(program: Program, *, entry: str | None = None) -> Scene:
    """Build a deterministic Scene from a parsed program.

    For v0.1.0 the only supported entry kind is a `bloom` declaration. The
    rendered scene wraps the resolved BloomInstance on a square canvas sized
    to the bloom's `size` property (or 200 by default).
    """
    palettes: dict[str, PaletteDecl] = {}
    for p in program.palettes:
        if p.name in palettes:
            raise FlorasNameError(p.line, f"palette '{p.name}' is already defined")
        palettes[p.name] = p

    blooms: dict[str, BloomDecl] = {}
    for b in program.blooms:
        if b.name in blooms:
            raise FlorasNameError(b.line, f"bloom '{b.name}' is already defined")
        blooms[b.name] = b

    if not blooms:
        raise FlorasValidationError(program.line, "program contains no bloom declaration")

    selected_name = _pick_entry(blooms, entry)
    bloom_decl = blooms[selected_name]

    palette_table = build_palette_table(palettes)
    instance = resolve_bloom(bloom_decl, palette_table)

    # The canvas size matches the bloom's footprint, with padding so the petal
    # tips and stem are not clipped.
    pad = max(8.0, instance.size * 0.05)
    width = instance.size + pad * 2
    bottom_pad = pad + (instance.stem_length if instance.stem else 0.0)
    height = instance.size + pad + bottom_pad
    centre_x = width / 2.0
    centre_y = pad + instance.size / 2.0
    instance = instance.with_position(centre_x, centre_y)

    return Scene(canvas=(width, height), background=None, items=(instance,))


def _pick_entry(blooms: dict[str, BloomDecl], entry: str | None) -> str:
    if entry is not None:
        if entry not in blooms:
            raise FlorasNameError(0, f"bloom '{entry}' is not defined")
        return entry
    if len(blooms) == 1:
        return next(iter(blooms))
    names = ", ".join(sorted(blooms))
    raise FlorasValidationError(
        0,
        f"file declares multiple blooms ({names}); pass --entry <name>",
    )
