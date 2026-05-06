"""SVG renderer — turn a Scene into a complete `<svg>` document."""

from __future__ import annotations

from floras.ast_nodes import HexColor
from floras.compose.scene import BloomInstance, Scene
from floras.geometry.leaf import leaf_path
from floras.geometry.petal import petal_path
from floras.geometry.stamen import stamen_positions
from floras.geometry.stem import stem_path

# Petals are authored at a canonical body radius. The bloom instance scales
# them via `transform="scale(...)"` to reach the requested size.
_PETAL_BODY_RADIUS = 100.0


def render_svg(scene: Scene) -> str:
    width, height = scene.canvas
    body: list[str] = []
    if scene.background is not None:
        body.append(
            f'  <rect width="{_n(width)}" height="{_n(height)}" '
            f'fill="{scene.background.hex}"/>'
        )
    for item in scene.items:
        body.append(_render_bloom(item))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(width)} {_n(height)}" '
        f'width="{_n(width)}" height="{_n(height)}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def _render_bloom(b: BloomInstance) -> str:
    scale = b.size / (2.0 * _PETAL_BODY_RADIUS)
    parts: list[str] = []

    # Stem (rendered first so flowers sit on top).
    if b.stem:
        parts.append(
            f'    <path class="stem" d="{stem_path(b.stem_length / scale)}" '
            f'stroke="{b.stem_color.hex}" stroke-width="{_n(2.0 / scale)}" '
            f'fill="none" stroke-linecap="round"/>'
        )

    if b.leaf_count > 0:
        parts.append(_render_leaves(b))

    # Petals.
    petal_d = petal_path(b.petal_width / scale, b.petal_height / scale, b.petal_curl, b.petal_notch)
    petal_attrs = [f'fill="{b.color.hex}"']
    if b.stroke_color is not None and b.stroke_width > 0.0:
        petal_attrs.append(f'stroke="{b.stroke_color.hex}"')
        petal_attrs.append(f'stroke-width="{_n(b.stroke_width / scale)}"')
        petal_attrs.append('stroke-linejoin="round"')

    petals_g = ['    <g class="petals">']
    angle = 0.0
    for _ in range(b.petals):
        petals_g.append(
            f'      <path d="{petal_d}" {" ".join(petal_attrs)} '
            f'transform="rotate({_n(angle)})"/>'
        )
        angle = (angle + b.arrange_rotation) % 360.0
    petals_g.append("    </g>")
    parts.append("\n".join(petals_g))

    # Stamens (drawn after petals so they sit on top in z-order).
    if b.stamen_count > 0:
        positions = stamen_positions(b.stamen_count, b.stamen_radius / scale)
        stamen_lines = [f'    <g class="stamens" fill="{b.stamen_color.hex}">']
        for sx, sy in positions:
            stamen_lines.append(
                f'      <circle cx="{_n(sx)}" cy="{_n(sy)}" r="{_n(2.5 / scale)}"/>'
            )
        stamen_lines.append("    </g>")
        parts.append("\n".join(stamen_lines))

    transform = (
        f'translate({_n(b.x)} {_n(b.y)}) '
        f'rotate({_n(b.rotation)}) '
        f'scale({_n(scale)})'
    )
    return (
        f'  <g class="bloom bloom-{b.bloom_name}" transform="{transform}">\n'
        + "\n".join(parts)
        + "\n  </g>"
    )


def _render_leaves(b: BloomInstance) -> str:
    lines = ['    <g class="leaves">']
    half_h = b.stem_length / 2.0
    leaf_w = b.size * 0.18 / (b.size / (2.0 * _PETAL_BODY_RADIUS))
    leaf_h = b.size * 0.32 / (b.size / (2.0 * _PETAL_BODY_RADIUS))
    d = leaf_path(leaf_w, leaf_h)
    fill = b.stem_color.hex
    for i in range(b.leaf_count):
        side = 1 if i % 2 == 0 else -1
        offset_y = (i + 1) * half_h / (b.leaf_count + 1)
        rot = -55 if side > 0 else 55
        lines.append(
            f'      <path d="{d}" fill="{fill}" '
            f'transform="translate(0 {_n(offset_y / (b.size / (2.0 * _PETAL_BODY_RADIUS)))}) '
            f'rotate({_n(rot)})"/>'
        )
    lines.append("    </g>")
    return "\n".join(lines)


def _n(value: float) -> str:
    """Format a float at 2 decimal places, dropping trailing zeros / dot."""
    formatted = f"{value:.2f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


# ``HexColor`` is only re-exported for type hints by callers; explicit re-export
# keeps mypy happy without an unused-import warning.
__all__ = ["HexColor", "render_svg"]
