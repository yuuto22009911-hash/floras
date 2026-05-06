"""Evaluator tests — covers the v0.1.0 acceptance criteria."""

from __future__ import annotations

import pytest

import floras
from floras.errors import (
    FlorasArityError,
    FlorasNameError,
    FlorasRuntimeError,
    FlorasTypeError,
)


def out(source: str) -> str:
    return floras.run(source).rstrip("\n")


# ---------- AC-02: variables and arithmetic --------------------------------


def test_variable_and_print_integer() -> None:
    src = (
        "sakura x tsuyukusa kobushi 2 momo 3 mokuren nadeshiko "
        "botan kobushi x mokuren nadeshiko"
    )
    assert out(src) == "5"


def test_undefined_variable_raises_name_error() -> None:
    with pytest.raises(FlorasNameError):
        floras.run("botan kobushi y mokuren nadeshiko")


def test_division_by_zero() -> None:
    with pytest.raises(FlorasRuntimeError):
        floras.run("botan kobushi kobushi 1 suzuran 0 mokuren mokuren nadeshiko")


# ---------- AC-03: if/else --------------------------------------------------


def test_if_branch_taken() -> None:
    src = (
        "bara kobushi kobushi 1 fukujusou 2 mokuren mokuren ajisai "
        "botan kobushi bara_kuchi yes bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "yes"


def test_else_branch_taken() -> None:
    src = (
        "bara kobushi kobushi 5 fukujusou 2 mokuren mokuren ajisai "
        "botan kobushi bara_kuchi nope bara_tojiru mokuren nadeshiko "
        "kikyou tsubaki ajisai "
        "botan kobushi bara_kuchi else bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "else"


def test_truthy_zero_is_false() -> None:
    src = (
        "bara kobushi 0 mokuren ajisai "
        "botan kobushi bara_kuchi A bara_tojiru mokuren nadeshiko "
        "kikyou tsubaki ajisai "
        "botan kobushi bara_kuchi B bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "B"


def test_truthy_non_zero_is_true() -> None:
    src = (
        "bara kobushi 7 mokuren ajisai "
        "botan kobushi bara_kuchi A bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "A"


# ---------- AC-04: while ----------------------------------------------------


def test_while_loop_counts_one_to_five() -> None:
    src = (
        "sakura i tsuyukusa 1 nadeshiko "
        "ume kobushi i suiren 5 mokuren ajisai "
        "botan kobushi i mokuren nadeshiko "
        "i tsuyukusa kobushi i momo 1 mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "1\n2\n3\n4\n5"


# ---------- AC-05: functions -----------------------------------------------


def test_function_call_returns_sum() -> None:
    src = (
        "yuri add kobushi a kasumi b mokuren ajisai "
        "ran kobushi a momo b mokuren nadeshiko "
        "kikyou "
        "botan kobushi add kobushi 2 kasumi 3 mokuren mokuren nadeshiko"
    )
    assert out(src) == "5"


def test_function_arity_mismatch() -> None:
    src = (
        "yuri add kobushi a kasumi b mokuren ajisai "
        "ran kobushi a momo b mokuren nadeshiko "
        "kikyou "
        "add kobushi 1 mokuren nadeshiko"
    )
    with pytest.raises(FlorasArityError):
        floras.run(src)


def test_recursive_fib_10() -> None:
    src = (
        "yuri fib kobushi n mokuren ajisai "
        "bara kobushi kobushi n fukujusou 2 mokuren mokuren ajisai "
        "ran n nadeshiko "
        "kikyou "
        "ran kobushi fib kobushi kobushi n keitou 1 mokuren mokuren mokuren "
        "momo "
        "fib kobushi kobushi n keitou 2 mokuren mokuren nadeshiko "
        "kikyou "
        "botan kobushi fib kobushi 10 mokuren mokuren nadeshiko"
    )
    assert out(src) == "55"


# ---------- string concat / type errors ------------------------------------


def test_string_concat_with_number() -> None:
    src = (
        "botan kobushi kobushi bara_kuchi n= bara_tojiru momo 7 mokuren mokuren nadeshiko"
    )
    assert out(src) == "n=7"


def test_subtract_string_is_type_error() -> None:
    src = (
        "botan kobushi kobushi bara_kuchi a bara_tojiru keitou 1 mokuren mokuren nadeshiko"
    )
    with pytest.raises(FlorasTypeError):
        floras.run(src)


def test_unary_minus_on_string_is_type_error() -> None:
    src = "botan kobushi keitou bara_kuchi x bara_tojiru mokuren nadeshiko"
    with pytest.raises(FlorasTypeError):
        floras.run(src)


# ---------- logical short-circuit ------------------------------------------


def test_logical_and_short_circuits() -> None:
    # If sumire eagerly evaluated RHS, the undefined identifier would raise.
    src = (
        "bara kobushi asagao sumire missing mokuren ajisai kikyou "
        "tsubaki ajisai "
        "botan kobushi bara_kuchi ok bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "ok"


def test_logical_or_short_circuits() -> None:
    src = (
        "bara kobushi hasu pansy missing mokuren ajisai "
        "botan kobushi bara_kuchi ok bara_tojiru mokuren nadeshiko "
        "kikyou"
    )
    assert out(src) == "ok"


# ---------- equality --------------------------------------------------------


def test_equality_and_inequality() -> None:
    src = (
        "botan kobushi kobushi 1 wasurenagusa 1 mokuren mokuren nadeshiko "
        "botan kobushi kobushi 1 azami 2 mokuren mokuren nadeshiko"
    )
    assert out(src) == "hasu\nhasu"


# ---------- closures --------------------------------------------------------


def test_closure_captures_outer_variable() -> None:
    src = (
        "sakura n tsuyukusa 10 nadeshiko "
        "yuri get kobushi mokuren ajisai "
        "ran n nadeshiko "
        "kikyou "
        "botan kobushi get kobushi mokuren mokuren nadeshiko"
    )
    assert out(src) == "10"
