from __future__ import annotations

import math
from decimal import Decimal

import pytest
from app.services.query import _json_safe_cell, _json_safe_row


@pytest.mark.parametrize(
    ("inp", "want"),
    [
        (1, 1),
        ("x", "x"),
        (float("nan"), None),
        (float("inf"), None),
        (float("-inf"), None),
    ],
)
def test_json_safe_cell_float_special(inp: object, want: object) -> None:
    assert _json_safe_cell(inp) == want


def test_json_safe_cell_decimal_nan() -> None:
    assert _json_safe_cell(Decimal("NaN")) is None


def test_json_safe_cell_decimal_inf() -> None:
    assert _json_safe_cell(Decimal("Infinity")) is None


def test_json_safe_row_maps_values() -> None:
    row = {"a": 1, "b": float("nan")}
    out = _json_safe_row(row)
    assert out["a"] == 1
    assert out["b"] is None


def test_json_safe_cell_normal_float() -> None:
    assert _json_safe_cell(3.14) == pytest.approx(3.14)
    assert _json_safe_cell(math.pi) == pytest.approx(math.pi)
