"""Optional integration tests: set POSTGRES_INTEGRATION_URL (e.g. CI service or docker-compose postgres)."""

from __future__ import annotations

import os

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def postgres_integration_url() -> str:
    url = os.getenv("POSTGRES_INTEGRATION_URL")
    if not url:
        pytest.skip("POSTGRES_INTEGRATION_URL not set (e.g. postgresql://postgres:postgres@127.0.0.1:5432/postgres)")
    return url


@pytest.mark.integration
def test_put_db_metadata_and_query(
    client: TestClient,
    postgres_integration_url: str,
) -> None:
    name = "integration_pg"
    r = client.put(
        f"/api/v1/dbs/{name}",
        json={"url": postgres_integration_url},
    )
    assert r.status_code in (200, 201), r.text

    r2 = client.get(f"/api/v1/dbs/{name}", params={"refresh": "true"})
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert "tables" in body

    r3 = client.post(
        f"/api/v1/dbs/{name}/query",
        json={"sql": "SELECT 1 AS one"},
    )
    assert r3.status_code == 200, r3.text
    q = r3.json()
    assert q.get("rowCount") == 1
    assert q.get("rows") == [{"one": 1}]  # API camelCase top-level; row keys from DB
