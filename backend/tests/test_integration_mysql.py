"""Integration tests for MySQL support.

Run with:  MYSQL_INTEGRATION_URL=mysql://root@localhost/todo_db pytest -m integration_mysql -v
"""
from __future__ import annotations

import os

import pytest

from app.services import connection as connection_service
from app.services import metadata as metadata_service
from app.services import query as query_service

MYSQL_URL = os.environ.get("MYSQL_INTEGRATION_URL", "")

pytestmark = pytest.mark.integration_mysql


@pytest.fixture()
def mysql_url() -> str:
    if not MYSQL_URL:
        pytest.skip("MYSQL_INTEGRATION_URL not set")
    return MYSQL_URL


@pytest.mark.asyncio
async def test_mysql_connection(mysql_url: str) -> None:
    await connection_service.test_mysql_connection(mysql_url)


@pytest.mark.asyncio
async def test_mysql_metadata(mysql_url: str) -> None:
    meta = await metadata_service.fetch_metadata_from_mysql(mysql_url)
    assert len(meta.tables) > 0
    for t in meta.tables:
        assert t.table_name
        assert len(t.columns) > 0


@pytest.mark.asyncio
async def test_mysql_query(mysql_url: str) -> None:
    result = await query_service.execute_select(mysql_url, "SELECT * FROM todos")
    assert result.row_count >= 0
    assert len(result.columns) > 0
    assert result.sql  # should contain LIMIT
