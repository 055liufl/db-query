from __future__ import annotations

from starlette.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert body.get("llmTransport") == "aiohttp"
    assert body.get("llmDns") == "socket_sync"


def test_list_dbs_empty(client: TestClient) -> None:
    r = client.get("/api/v1/dbs")
    assert r.status_code == 200
    assert r.json() == []


def test_put_db_invalid_url(client: TestClient) -> None:
    r = client.put(
        "/api/v1/dbs/smoke-db",
        json={"url": "http://example.com/not-postgres"},
    )
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert "message" in body


def test_get_metadata_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/dbs/no-such-connection")
    assert r.status_code == 404
    body = r.json()
    assert body.get("error") == "connection_not_found"


def test_natural_query_connection_not_found(client: TestClient) -> None:
    r = client.post(
        "/api/v1/dbs/missing/query/natural",
        json={"prompt": "select 1"},
    )
    assert r.status_code == 404
    assert r.json().get("error") == "connection_not_found"
