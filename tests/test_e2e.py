"""End-to-end tests: run example .floras files and compare to fixtures."""

from __future__ import annotations

from pathlib import Path

import floras

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_hello_example() -> None:
    source = (EXAMPLES / "hello.floras").read_text(encoding="utf-8")
    assert floras.run(source) == "Hello, world\n"


def test_fizzbuzz_example_matches_canonical_output() -> None:
    source = (EXAMPLES / "fizzbuzz.floras").read_text(encoding="utf-8")

    expected_lines: list[str] = []
    for i in range(1, 16):
        if i % 15 == 0:
            expected_lines.append("FizzBuzz")
        elif i % 3 == 0:
            expected_lines.append("Fizz")
        elif i % 5 == 0:
            expected_lines.append("Buzz")
        else:
            expected_lines.append(str(i))
    expected = "\n".join(expected_lines) + "\n"

    assert floras.run(source) == expected


def test_fib_example() -> None:
    source = (EXAMPLES / "fib.floras").read_text(encoding="utf-8")
    assert floras.run(source).strip() == "55"
