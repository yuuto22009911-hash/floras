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


def test_no_alphabet_in_any_example_source() -> None:
    """The DSL surface must contain no ASCII alphabet characters at all.

    File-path strings inside ``書出 ... へ "..."`` would technically be allowed
    to contain alphabet, but our v0.1.0 examples don't use ``書出`` yet, so we
    can assert on the entire source.
    """
    import re

    for path in sorted(EXAMPLES.glob("*.bloom")):
        source = path.read_text(encoding="utf-8")
        # Strip out anything inside double-quoted strings before checking.
        scrubbed = re.sub(r'"[^"]*"', "", source)
        assert not re.search(r"[A-Za-z]", scrubbed), (
            f"{path.name} contains alphabet characters in DSL surface"
        )
