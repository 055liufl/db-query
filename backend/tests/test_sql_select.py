from __future__ import annotations

import pytest
from app.services.sql_select import parse_single_select_statement


def test_parse_single_select_ok() -> None:
    stmt = parse_single_select_statement("SELECT 1 AS x")
    assert stmt is not None


def test_parse_rejects_non_select() -> None:
    with pytest.raises(ValueError, match="仅允许执行 SELECT"):
        parse_single_select_statement("DELETE FROM t")


def test_parse_rejects_union() -> None:
    with pytest.raises(ValueError, match="UNION"):
        parse_single_select_statement("SELECT 1 UNION SELECT 2")
