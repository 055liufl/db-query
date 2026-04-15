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
    ["", "http://localhost"],
)
def test_validate_postgres_url_bad(url: str) -> None:
    with pytest.raises(ValueError):
        connection_service.validate_postgres_url(url)


def test_detect_db_type_postgres() -> None:
    assert connection_service.detect_db_type("postgres://u:p@localhost:5432/db") == "postgres"
    assert connection_service.detect_db_type("postgresql://u:p@localhost:5432/db") == "postgres"


def test_detect_db_type_mysql() -> None:
    assert connection_service.detect_db_type("mysql://u:p@localhost:3306/db") == "mysql"


def test_detect_db_type_unknown() -> None:
    with pytest.raises(ValueError, match="mysql://"):
        connection_service.detect_db_type("http://localhost")


def test_validate_db_url_postgres() -> None:
    assert connection_service.validate_db_url("postgres://u:p@localhost:5432/db") == "postgres"


def test_validate_db_url_mysql() -> None:
    assert connection_service.validate_db_url("mysql://root@localhost:3306/todo_db") == "mysql"


def test_validate_db_url_bad() -> None:
    with pytest.raises(ValueError):
        connection_service.validate_db_url("http://localhost")


def test_parse_mysql_url_full() -> None:
    params = connection_service._parse_mysql_url("mysql://root:pass@myhost:3307/mydb")
    assert params["host"] == "myhost"
    assert params["port"] == 3307
    assert params["user"] == "root"
    assert params["password"] == "pass"
    assert params["db"] == "mydb"


def test_parse_mysql_url_defaults() -> None:
    params = connection_service._parse_mysql_url("mysql://root@localhost/todo_db")
    assert params["host"] == "localhost"
    assert params["port"] == 3306
    assert params["user"] == "root"
    assert params["password"] == ""
    assert params["db"] == "todo_db"
