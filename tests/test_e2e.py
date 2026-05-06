"""End-to-end render tests for every example .bloom file."""

from __future__ import annotations

from pathlib import Path

import floras

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_all_examples_render_without_error() -> None:
    for path in sorted(EXAMPLES.glob("*.bloom")):
        source = path.read_text(encoding="utf-8")
        svg = floras.render(source)
        assert svg.startswith("<svg "), f"{path.name} did not produce an SVG"
        assert svg.count("<path") >= 1, f"{path.name} produced no paths"


def test_examples_render_deterministically() -> None:
    for path in sorted(EXAMPLES.glob("*.bloom")):
        source = path.read_text(encoding="utf-8")
        first = floras.render(source)
        second = floras.render(source)
        assert first == second, f"{path.name} render is non-deterministic"
