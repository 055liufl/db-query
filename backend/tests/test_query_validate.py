from __future__ import annotations

import pytest

from app.services.query import validate_and_prepare_sql


def test_select_one_adds_limit() -> None:
    sql, missing = validate_and_prepare_sql("SELECT 1 AS one")
    assert "LIMIT" in sql.upper()
    assert missing is True


def test_select_with_limit_unchanged() -> None:
    sql, missing = validate_and_prepare_sql("SELECT 1 AS one LIMIT 10")
    assert "LIMIT 10" in sql.upper() or "limit 10" in sql.lower()
    assert missing is False


def test_rejects_drop() -> None:
    with pytest.raises(ValueError, match="SELECT|仅允许"):
        validate_and_prepare_sql("DROP TABLE users")


def test_rejects_multiple_statements() -> None:
    with pytest.raises(ValueError, match="一条"):
        validate_and_prepare_sql("SELECT 1; SELECT 2")


def test_rejects_union() -> None:
    with pytest.raises(ValueError, match="UNION"):
        validate_and_prepare_sql("SELECT 1 UNION SELECT 2")
