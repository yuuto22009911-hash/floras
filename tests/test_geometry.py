"""Geometry path generator tests."""

from __future__ import annotations

import math

from floras.geometry.leaf import leaf_path
from floras.geometry.petal import petal_path
from floras.geometry.stamen import stamen_positions
from floras.geometry.stem import stem_path


def test_petal_path_simple_no_notch_starts_and_closes_at_origin() -> None:
    d = petal_path(width=40, height=80, curl=0.4, notch=0.0)
    assert d.startswith("M 0 0")
    assert d.endswith("Z")
    assert "0 -80" in d  # tip vertex appears verbatim


def test_petal_path_with_notch_includes_inner_vertex() -> None:
    d = petal_path(width=40, height=80, curl=0.4, notch=0.5)
    # The notch form uses two `L` segments to draw the V-shaped tip.
    assert d.count(" L ") >= 2


def test_stamen_positions_count_and_radius() -> None:
    positions = stamen_positions(count=12, radius=10.0)
    assert len(positions) == 12
    for x, y in positions:
        assert math.isclose(math.hypot(x, y), 10.0, rel_tol=1e-6)


def test_stamen_positions_zero_count_returns_empty() -> None:
    assert stamen_positions(0, 5.0) == []


def test_leaf_path_round_trips_origin() -> None:
    d = leaf_path(20.0, 60.0)
    assert d.startswith("M 0 0") and d.endswith("Z")


def test_stem_path_is_a_vertical_line() -> None:
    d = stem_path(50.0)
    assert d == "M 0 0 L 0 50.00"
