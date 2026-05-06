"""Procedural scatter expansion (`散らす`) — deterministic given a seed."""

from __future__ import annotations

import math
from random import Random

from floras.ast_nodes import (
    AreaCanvas,
    AreaGrid,
    AreaRect,
    AreaRing,
    AreaSpec,
    BloomDecl,
    Coord,
    HexColor,
    Placement,
    Range,
    ScatterDecl,
    StrokeSpec,
    Value,
)
from floras.compose.resolver import resolve_placement
from floras.compose.scene import BloomInstance
from floras.errors import FlorasNameError, FlorasValidationError


def expand_scatter(
    scatter: ScatterDecl,
    blooms: dict[str, BloomDecl],
    palettes: dict[str, dict[str, HexColor]],
    canvas_width: float,
    canvas_height: float,
) -> list[BloomInstance]:
    """Turn a `散らす` declaration into a deterministic list of BloomInstances."""
    if scatter.source not in blooms:
        raise FlorasNameError(
            scatter.line, f"bloom '{scatter.source}' is not defined"
        )
    bloom_decl = blooms[scatter.source]

    rng = Random(scatter.seed)
    positions = _generate_positions(scatter.area, scatter.count, rng, canvas_width, canvas_height)

    instances: list[BloomInstance] = []
    for x, y in positions:
        overrides: dict[str, Value | StrokeSpec] = {}
        if scatter.size is not None:
            overrides["大きさ"] = _resolve_range_or_value(scatter.size, rng)
        if scatter.rotation is not None:
            overrides["回転"] = _resolve_range_or_value(scatter.rotation, rng, default_min=0.0, default_max=360.0)
        if scatter.color is not None:
            overrides["色"] = scatter.color  # ColorValue not affected by RNG (palette tint amount is fixed)

        placement = Placement(
            target=scatter.source,
            coord=_make_coord(x, y),
            overrides=overrides,
            line=scatter.line,
        )
        instances.append(
            resolve_placement(
                bloom_decl,
                placement,
                palettes,
                canvas_width,
                canvas_height,
            )
        )
    return instances


# --------------------------------------------------------------------------
# Position generation
# --------------------------------------------------------------------------


def _generate_positions(
    area: AreaSpec,
    count: int | str,
    rng: Random,
    canvas_w: float,
    canvas_h: float,
) -> list[tuple[float, float]]:
    if isinstance(area, AreaCanvas):
        n = _resolve_count(count, default_grid=None, line=0)
        return [
            (rng.uniform(0.0, canvas_w), rng.uniform(0.0, canvas_h))
            for _ in range(n)
        ]
    if isinstance(area, AreaRing):
        n = _resolve_count(count, default_grid=None, line=0)
        return [_sample_ring(area, rng) for _ in range(n)]
    if isinstance(area, AreaRect):
        n = _resolve_count(count, default_grid=None, line=0)
        return [
            (rng.uniform(area.x1, area.x2), rng.uniform(area.y1, area.y2))
            for _ in range(n)
        ]
    if isinstance(area, AreaGrid):
        n = _resolve_count(count, default_grid=area.cols * area.rows, line=0)
        # Snap to a regular grid; if `n` is fewer than cells, take the first
        # ones in row-major order.
        cells: list[tuple[float, float]] = []
        cw = canvas_w / max(area.cols, 1)
        ch = canvas_h / max(area.rows, 1)
        for r in range(area.rows):
            for c in range(area.cols):
                cells.append((cw * (c + 0.5), ch * (r + 0.5)))
        return cells[:n]
    raise FlorasValidationError(0, f"unsupported area spec: {area!r}")


def _sample_ring(ring: AreaRing, rng: Random) -> tuple[float, float]:
    radius = rng.uniform(ring.inner, ring.outer)
    theta = rng.uniform(0.0, 2.0 * math.pi)
    return (
        ring.center_x + radius * math.cos(theta),
        ring.center_y + radius * math.sin(theta),
    )


def _resolve_count(count: int | str, *, default_grid: int | None, line: int) -> int:
    if isinstance(count, int):
        if count < 0:
            raise FlorasValidationError(line, "scatter count must be >= 0")
        return count
    if count == "自動":
        if default_grid is None:
            raise FlorasValidationError(
                line, "'数 自動' is only valid for grid areas"
            )
        return default_grid
    raise FlorasValidationError(line, f"unsupported scatter count: {count!r}")


# --------------------------------------------------------------------------
# Override value sampling
# --------------------------------------------------------------------------


def _resolve_range_or_value(
    v: Value,
    rng: Random,
    *,
    default_min: float | None = None,
    default_max: float | None = None,
) -> Value:
    """Sample a range, or evaluate `乱数` to a uniform float, or pass through."""
    from floras.ast_nodes import IdentValue, NumberValue  # noqa: PLC0415

    if isinstance(v, Range):
        return NumberValue(value=rng.uniform(v.min, v.max), line=v.line)
    if isinstance(v, IdentValue) and v.name == "乱数":
        if default_min is None or default_max is None:
            raise FlorasValidationError(
                v.line, "'乱数' here requires an implicit range"
            )
        return NumberValue(value=rng.uniform(default_min, default_max), line=v.line)
    return v


def _make_coord(x: float, y: float) -> Coord:
    return Coord(x=x, y=y)
