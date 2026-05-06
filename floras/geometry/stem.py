"""Stem — a vertical line below the flower."""

from __future__ import annotations


def stem_path(length: float) -> str:
    """Return the `d` attribute for a straight stem hanging below the origin."""
    return f"M 0 0 L 0 {length:.2f}"
