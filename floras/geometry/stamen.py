"""Stamen layout — small dots arranged in a ring around the flower centre."""

from __future__ import annotations

import math


def stamen_positions(count: int, radius: float) -> list[tuple[float, float]]:
    """Return (x, y) coordinates for `count` evenly spaced stamens on a ring."""
    if count <= 0:
        return []
    return [
        (
            radius * math.cos(2.0 * math.pi * i / count - math.pi / 2.0),
            radius * math.sin(2.0 * math.pi * i / count - math.pi / 2.0),
        )
        for i in range(count)
    ]
