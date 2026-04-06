from __future__ import annotations

import pytest

from app.services import connection as connection_service


def test_validate_name_ok() -> None:
    connection_service.validate_connection_name("my-postgres")


@pytest.mark.parametrize(
    "name",
    ["", "a" * 65, "bad name", "中文"],
)
def test_validate_name_bad(name: str) -> None:
    with pytest.raises(ValueError):
        connection_service.validate_connection_name(name)


def test_validate_postgres_url_ok() -> None:
    connection_service.validate_postgres_url("postgres://u:p@localhost:5432/db")


@pytest.mark.parametrize(
    "url",
    ["", "mysql://localhost/db", "http://localhost"],
)
def test_validate_postgres_url_bad(url: str) -> None:
    with pytest.raises(ValueError):
        connection_service.validate_postgres_url(url)
