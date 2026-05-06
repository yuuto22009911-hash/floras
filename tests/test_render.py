"""SVG renderer tests."""

from __future__ import annotations

import re

import floras


def _render(source: str) -> str:
    return floras.render(source)


def test_render_emits_complete_svg_document() -> None:
    svg = _render("bloom s { petals 5; size 200; color #FFB7C5; }")
    assert svg.startswith("<svg ")
    assert svg.rstrip().endswith("</svg>")
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg
    assert "viewBox=" in svg


def test_render_includes_one_path_per_petal() -> None:
    svg = _render("bloom s { petals 7; size 200; color #FFB7C5; }")
    petal_count = svg.count('<path d="M 0 0')
    # Each petal contributes one <path>; some other paths (stem, leaves) may
    # also exist but stem/leaves are off by default.
    assert petal_count == 7


def test_render_inserts_stamen_circles() -> None:
    svg = _render("bloom s { petals 5; stamen-count 8; }")
    assert svg.count("<circle") == 8


def test_render_with_stem_includes_stem_path() -> None:
    svg = _render("bloom s { petals 5; stem true; stem-length 100; }")
    assert 'class="stem"' in svg


def test_render_is_deterministic() -> None:
    src = "bloom s { petals 5; size 200; color #FFB7C5; petal-curl 0.4; petal-notch 0.3; }"
    a = _render(src)
    b = _render(src)
    assert a == b


def test_render_applies_stroke() -> None:
    svg = _render(
        "bloom s { petals 5; size 200; color #FFB7C5; stroke #2C2825 width 1.2; }"
    )
    assert 'stroke="#2C2825"' in svg


def test_coordinates_are_rounded_to_two_decimals() -> None:
    svg = _render("bloom s { petals 5; }")
    # No coordinate should have more than two digits after the decimal point.
    assert re.search(r"\d+\.\d{3,}", svg) is None
