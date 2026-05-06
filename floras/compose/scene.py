"""SceneGraph — the deterministic intermediate representation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TypeAlias

from floras.ast_nodes import HexColor


@dataclass(frozen=True)
class BloomInstance:
    bloom_name: str
    x: float
    y: float
    size: float
    rotation: float
    color: HexColor
    petals: int
    petal_width: float
    petal_height: float
    petal_curl: float
    petal_notch: float
    stamen_count: int
    stamen_radius: float
    stamen_color: HexColor
    stem: bool
    stem_length: float
    stem_color: HexColor
    leaf_count: int
    arrange: str
    arrange_rotation: float
    stroke_color: HexColor | None
    stroke_width: float

    def with_position(self, x: float, y: float) -> BloomInstance:
        return replace(self, x=x, y=y)


SceneItem: TypeAlias = BloomInstance


@dataclass(frozen=True)
class Scene:
    canvas: tuple[float, float]
    background: HexColor | None
    items: tuple[SceneItem, ...]
