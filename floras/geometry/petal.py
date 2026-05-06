"""Petal path generator — a single symmetric petal as an SVG path string.

The petal is drawn with its base at the origin (0, 0) and the tip pointing
up (negative Y in SVG coordinates). Callers translate / rotate / scale the
returned path to position the petal around a flower's centre.
"""

from __future__ import annotations


def petal_path(width: float, height: float, curl: float, notch: float) -> str:
    """Return the `d` attribute for a single petal `<path>`.

    Parameters
    ----------
    width
        Maximum half-width at the petal's widest point (the body bulge).
    height
        Total length from base to tip.
    curl
        Bulge factor in [0, 1]. 0 = thin almond, 1 = round bulb.
    notch
        Tip inset in [0, 1]. 0 = sharp tip, 1 = deep V-cut (sakura/cherry).

    The path uses two cubic bezier segments meeting at the tip. When
    `notch > 0`, two additional segments form the notch.
    """
    # Half-width of the bulge.
    half_w = width * 0.5
    # Vertical placement of the bulge (closer to the base looks bulbier).
    bulge_y = -height * (0.55 - 0.15 * curl)
    # Outward control point distance from the centre line at the bulge.
    bulge_x = half_w * (0.6 + 0.8 * curl)
    # The control points just below the tip control how sharp the tip looks.
    tip_pull = height * (0.10 + 0.20 * curl)
    tip_x = half_w * 0.45 * (1.0 - notch)

    if notch <= 0.0:
        # Single tip point — two cubic curves meeting at (0, -height).
        return (
            f"M 0 0 "
            f"C {bulge_x:.2f} {bulge_y * 0.5:.2f}, "
            f"{tip_x:.2f} {-height + tip_pull:.2f}, "
            f"0 {-height:.2f} "
            f"C {-tip_x:.2f} {-height + tip_pull:.2f}, "
            f"{-bulge_x:.2f} {bulge_y * 0.5:.2f}, "
            f"0 0 Z"
        )

    # With a notch: insert a centre dip just before the tip on each side.
    notch_depth = height * 0.06 * notch
    notch_x = half_w * 0.18 * notch
    return (
        f"M 0 0 "
        f"C {bulge_x:.2f} {bulge_y * 0.5:.2f}, "
        f"{tip_x:.2f} {-height + tip_pull:.2f}, "
        f"{notch_x:.2f} {-height + notch_depth:.2f} "
        f"L 0 {-height + notch_depth * 1.6:.2f} "
        f"L {-notch_x:.2f} {-height + notch_depth:.2f} "
        f"C {-tip_x:.2f} {-height + tip_pull:.2f}, "
        f"{-bulge_x:.2f} {bulge_y * 0.5:.2f}, "
        f"0 0 Z"
    )
