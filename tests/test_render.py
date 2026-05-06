"""SVG renderer tests."""

from __future__ import annotations

import re

import floras


def _render(source: str) -> str:
    return floras.render(source)


def test_render_emits_complete_svg_document() -> None:
    svg = _render("花 さくら { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); }")
    assert svg.startswith("<svg ")
    assert svg.rstrip().endswith("</svg>")
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg
    assert "viewBox=" in svg


def test_render_includes_one_path_per_petal() -> None:
    svg = _render("花 さくら { 花弁数 7; 色 知覚色(0.85 0.10 12); }")
    petal_count = svg.count('<path d="M 0 0')
    assert petal_count == 7


def test_render_inserts_stamen_circles() -> None:
    svg = _render("花 さくら { 花弁数 5; 雄蕊数 8; 色 知覚色(0.85 0.10 12); }")
    assert svg.count("<circle") == 8


def test_render_with_stem_includes_stem_path() -> None:
    svg = _render(
        "花 さくら { 花弁数 5; 茎 真; 茎丈 100; 色 知覚色(0.85 0.10 12); }"
    )
    assert 'class="stem"' in svg


def test_render_is_deterministic() -> None:
    src = (
        "花 さくら { 花弁数 5; 大きさ 200; 色 知覚色(0.85 0.10 12); "
        "花弁反り 0.4; 花弁切込 0.3; }"
    )
    a = _render(src)
    b = _render(src)
    assert a == b


def test_render_applies_stroke() -> None:
    svg = _render(
        "花 さくら { 花弁数 5; 色 知覚色(0.85 0.10 12); "
        "輪郭 知覚色(0.20 0.02 30) 幅 1.2; }"
    )
    # The stroke attribute is some hex resulting from the OKLCH conversion;
    # we just confirm the attribute is emitted.
    assert 'stroke="#' in svg


def test_coordinates_are_rounded_to_two_decimals() -> None:
    svg = _render("花 さくら { 花弁数 5; 色 知覚色(0.85 0.10 12); }")
    assert re.search(r"\d+\.\d{3,}", svg) is None


def test_bouquet_renders_two_blooms_on_one_canvas() -> None:
    src = (
        "花 さくら { 花弁数 5; 大きさ 100; 色 知覚色(0.85 0.10 12); }\n"
        "花束 束 { 画布 600 × 400; 置く さくら に (200, 200); 置く さくら に (400, 200); }"
    )
    svg = _render(src)
    assert svg.count('class="bloom') == 2
    assert 'viewBox="0 0 600 400"' in svg
