"""Leaf path generator — a simple lance-shaped path."""

from __future__ import annotations


def leaf_path(width: float, height: float) -> str:
    """Return the `d` attribute for a leaf `<path>` rooted at the origin."""
    half_w = width * 0.5
    mid_y = -height * 0.55
    return (
        f"M 0 0 "
        f"C {half_w:.2f} {mid_y:.2f}, "
        f"{half_w * 0.4:.2f} {-height:.2f}, "
        f"0 {-height:.2f} "
        f"C {-half_w * 0.4:.2f} {-height:.2f}, "
        f"{-half_w:.2f} {mid_y:.2f}, "
        f"0 0 Z"
    )
