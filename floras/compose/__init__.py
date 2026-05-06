"""Compose pipeline: AST → resolved SceneGraph."""

from __future__ import annotations

from floras.ast_nodes import (
    BloomDecl,
    BouquetDecl,
    Coord,
    HexColor,
    MotifDecl,
    PaletteDecl,
    Placement,
    Program,
)
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

    The entry point may be the name of a `bloom` (rendered on a square
    auto-sized canvas) or a `bouquet` (rendered on the bouquet's declared
    canvas with all its placements and scatters).
    """
    palettes = _index_palettes(program.palettes)
    blooms = _index_blooms(program.blooms)
    motifs = _index_motifs(program.motifs)
    bouquets = _index_bouquets(program.bouquets)

    if not blooms and not bouquets:
        raise FlorasValidationError(
            program.line, "program contains no bloom or bouquet declaration"
        )

    palette_table = build_palette_table(palettes)
    selected_kind, selected_name = _pick_entry(blooms, bouquets, entry)
    if selected_kind == "bouquet":
        return _compose_bouquet(
            bouquets[selected_name], blooms, motifs, palette_table
        )
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


def _index_motifs(decls: list[MotifDecl]) -> dict[str, MotifDecl]:
    out: dict[str, MotifDecl] = {}
    for m in decls:
        if m.name in out:
            raise FlorasNameError(m.line, f"motif '{m.name}' is already defined")
        out[m.name] = m
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
    motifs: dict[str, MotifDecl],
    palettes: dict[str, dict[str, HexColor]],
) -> Scene:
    if decl.canvas_width <= 0 or decl.canvas_height <= 0:
        raise FlorasValidationError(
            decl.line, "bouquet canvas width and height must be positive"
        )

    background = None
    if decl.background is not None:
        from floras.compose.resolver import _color_to_hex  # noqa: PLC0415

        background = _color_to_hex(decl.background, palettes)

    items: list[BloomInstance] = []
    # Scatters render first so explicit `置く`s layer on top.
    for scatter in decl.scatters:
        items.extend(
            expand_scatter(
                scatter,
                blooms,
                motifs,
                palettes,
                decl.canvas_width,
                decl.canvas_height,
            )
        )
    for placement in decl.placements:
        items.extend(
            _expand_placement(
                placement,
                blooms,
                motifs,
                palettes,
                decl.canvas_width,
                decl.canvas_height,
            )
        )

    return Scene(
        canvas=(decl.canvas_width, decl.canvas_height),
        background=background,
        items=tuple(items),
    )


def _expand_placement(
    placement: Placement,
    blooms: dict[str, BloomDecl],
    motifs: dict[str, MotifDecl],
    palettes: dict[str, dict[str, HexColor]],
    canvas_width: float,
    canvas_height: float,
    *,
    visiting: frozenset[str] = frozenset(),
) -> list[BloomInstance]:
    """Resolve a placement, expanding motif targets recursively."""
    target = placement.target
    if target in motifs:
        if target in visiting:
            chain = " -> ".join([*visiting, target])
            raise FlorasValidationError(
                placement.line,
                f"circular motif reference detected: {chain}",
            )
        if placement.coord.is_center:
            base_x = canvas_width / 2.0
            base_y = canvas_height / 2.0
        else:
            assert placement.coord.x is not None and placement.coord.y is not None
            base_x = placement.coord.x
            base_y = placement.coord.y
        out: list[BloomInstance] = []
        for inner in motifs[target].placements:
            shifted = _translate_placement(inner, base_x, base_y)
            out.extend(
                _expand_placement(
                    shifted,
                    blooms,
                    motifs,
                    palettes,
                    canvas_width,
                    canvas_height,
                    visiting=visiting | {target},
                )
            )
        return out
    if target not in blooms:
        raise FlorasNameError(
            placement.line, f"'{target}' is not a defined bloom or motif"
        )
    instance = resolve_placement(
        blooms[target], placement, palettes, canvas_width, canvas_height
    )
    return [instance]


def _translate_placement(
    placement: Placement, dx: float, dy: float
) -> Placement:
    """Shift a placement's coordinate by (dx, dy). `中央` becomes (dx, dy)."""
    if placement.coord.is_center:
        new_coord = Coord(x=dx, y=dy, line=placement.coord.line)
    else:
        assert placement.coord.x is not None and placement.coord.y is not None
        new_coord = Coord(
            x=placement.coord.x + dx,
            y=placement.coord.y + dy,
            line=placement.coord.line,
        )
    return Placement(
        target=placement.target,
        coord=new_coord,
        overrides=dict(placement.overrides),
        line=placement.line,
    )


