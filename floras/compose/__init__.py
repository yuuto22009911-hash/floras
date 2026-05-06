"""Compose pipeline: AST → resolved SceneGraph."""

from __future__ import annotations

from floras.ast_nodes import BloomDecl, BouquetDecl, HexColor, PaletteDecl, Program
from floras.compose.resolver import (
    build_palette_table,
    resolve_bloom,
    resolve_placement,
)
from floras.compose.scatter import expand_scatter
from floras.compose.scene import BloomInstance, Scene
from floras.errors import FlorasNameError, FlorasValidationError


def compose(program: Program, *, entry: str | None = None) -> Scene:
    """Build a deterministic Scene from a parsed program.

    The entry point may be the name of either a `bloom` (rendered on a square
    auto-sized canvas) or a `bouquet` (rendered on the bouquet's declared
    canvas with all its placements).
    """
    palettes = _index_palettes(program.palettes)
    blooms = _index_blooms(program.blooms)
    bouquets = _index_bouquets(program.bouquets)

    if not blooms and not bouquets:
        raise FlorasValidationError(
            program.line, "program contains no bloom or bouquet declaration"
        )

    palette_table = build_palette_table(palettes)
    selected_kind, selected_name = _pick_entry(blooms, bouquets, entry)
    if selected_kind == "bouquet":
        return _compose_bouquet(bouquets[selected_name], blooms, palette_table)
    return _compose_single_bloom(blooms[selected_name], palette_table)


def _index_palettes(decls: list[PaletteDecl]) -> dict[str, PaletteDecl]:
    out: dict[str, PaletteDecl] = {}
    for p in decls:
        if p.name in out:
            raise FlorasNameError(p.line, f"palette '{p.name}' is already defined")
        out[p.name] = p
    return out


def _index_blooms(decls: list[BloomDecl]) -> dict[str, BloomDecl]:
    out: dict[str, BloomDecl] = {}
    for b in decls:
        if b.name in out:
            raise FlorasNameError(b.line, f"bloom '{b.name}' is already defined")
        out[b.name] = b
    return out


def _index_bouquets(decls: list[BouquetDecl]) -> dict[str, BouquetDecl]:
    out: dict[str, BouquetDecl] = {}
    for b in decls:
        if b.name in out:
            raise FlorasNameError(b.line, f"bouquet '{b.name}' is already defined")
        out[b.name] = b
    return out


def _pick_entry(
    blooms: dict[str, BloomDecl],
    bouquets: dict[str, BouquetDecl],
    entry: str | None,
) -> tuple[str, str]:
    if entry is not None:
        if entry in bouquets:
            return "bouquet", entry
        if entry in blooms:
            return "bloom", entry
        raise FlorasNameError(0, f"'{entry}' is not a defined bloom or bouquet")

    # A single bouquet always wins: helper blooms typically accompany it. Only
    # when there are no bouquets do we fall back to picking a bloom directly.
    if len(bouquets) == 1:
        name = next(iter(bouquets))
        return "bouquet", name
    if not bouquets and len(blooms) == 1:
        name = next(iter(blooms))
        return "bloom", name

    candidates = list(bouquets) + list(blooms)
    names = ", ".join(sorted(candidates))
    raise FlorasValidationError(
        0,
        f"file declares multiple top-level entries ({names}); pass --entry <name>",
    )


def _compose_single_bloom(
    decl: BloomDecl, palettes: dict[str, dict[str, HexColor]]
) -> Scene:
    instance = resolve_bloom(decl, palettes)
    pad = max(8.0, instance.size * 0.05)
    width = instance.size + pad * 2
    bottom_pad = pad + (instance.stem_length if instance.stem else 0.0)
    height = instance.size + pad + bottom_pad
    centre_x = width / 2.0
    centre_y = pad + instance.size / 2.0
    instance = instance.with_position(centre_x, centre_y)
    return Scene(canvas=(width, height), background=None, items=(instance,))


def _compose_bouquet(
    decl: BouquetDecl,
    blooms: dict[str, BloomDecl],
    palettes: dict[str, dict[str, HexColor]],
) -> Scene:
    if decl.canvas_width <= 0 or decl.canvas_height <= 0:
        raise FlorasValidationError(
            decl.line, "bouquet canvas width and height must be positive"
        )

    background = None
    if decl.background is not None:
        from floras.compose.resolver import _color_to_hex

        background = _color_to_hex(decl.background, palettes)

    items: list[BloomInstance] = []
    # Scatters are rendered first so that explicit `place`d blooms layer on top.
    for scatter in decl.scatters:
        items.extend(
            expand_scatter(
                scatter, blooms, palettes, decl.canvas_width, decl.canvas_height
            )
        )
    for placement in decl.placements:
        if placement.target not in blooms:
            raise FlorasNameError(
                placement.line, f"bloom '{placement.target}' is not defined"
            )
        bloom_decl = blooms[placement.target]
        instance = resolve_placement(
            bloom_decl, placement, palettes, decl.canvas_width, decl.canvas_height
        )
        items.append(instance)

    return Scene(
        canvas=(decl.canvas_width, decl.canvas_height),
        background=background,
        items=tuple(items),
    )
