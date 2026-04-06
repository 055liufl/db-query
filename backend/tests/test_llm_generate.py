from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.models.metadata import DbMetadataResponse
from app.services import llm as llm_mod
from app.services.llm import (
    NaturalQueryUnusableError,
    _normalize_llm_select_fragment,
    generate_select_sql,
)
from app.storage import sqlite as sqlite_storage


def test_normalize_llm_select_fragment_prepends_select() -> None:
    raw = "email, display_name, created_at FROM public.users"
    out = _normalize_llm_select_fragment(raw)
    assert out == "SELECT email, display_name, created_at FROM public.users"


def test_normalize_llm_select_fragment_leaves_select_and_with() -> None:
    assert _normalize_llm_select_fragment("SELECT 1") == "SELECT 1"
    assert _normalize_llm_select_fragment("  select 1") == "select 1"
    with_sql = "WITH x AS (SELECT 1) SELECT * FROM x"
    assert _normalize_llm_select_fragment(with_sql) == with_sql


def _fake_llm_session_factory() -> type:
    class FakeResp:
        status = 200

        def __init__(self, body: str) -> None:
            self._body = body

        async def text(self) -> str:
            return self._body

        async def __aenter__(self) -> FakeResp:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

    class FakeSession:
        def __init__(self, body: str) -> None:
            self._body = body

        def post(self, *_a: object, **_kw: object) -> FakeResp:
            return FakeResp(self._body)

    return FakeSession


@pytest.mark.asyncio
async def test_generate_select_sql_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DB_QUERY_PATH", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    sqlite_storage.configure(tmp_path / "db_query.db")
    sqlite_storage.init_db()
    sqlite_storage.upsert_connection(
        "pg",
        "postgresql://u:p@127.0.0.1:5432/db",
        is_new=True,
    )
    meta = DbMetadataResponse(
        connection_name="pg",
        tables=[],
        cached_at=datetime.now(UTC),
    )
    sqlite_storage.save_metadata("pg", meta.model_dump_json(by_alias=True))

    FakeSession = _fake_llm_session_factory()
    body = '{"choices":[{"message":{"content":"SELECT 1"}}]}'

    async def fake_get_session(_settings: object) -> FakeSession:
        return FakeSession(body)

    monkeypatch.setattr(llm_mod, "_get_aio_session", fake_get_session)

    try:
        out = await generate_select_sql("pg", "hello")
        assert "SELECT" in out.upper()
    finally:
        await llm_mod.close_openai_client()


@pytest.mark.asyncio
async def test_generate_select_sql_accepts_fragment_missing_select_keyword(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Models sometimes return `cols FROM t` without SELECT; we normalize before parse."""
    monkeypatch.setenv("DB_QUERY_PATH", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    sqlite_storage.configure(tmp_path / "db_query.db")
    sqlite_storage.init_db()
    sqlite_storage.upsert_connection(
        "pg",
        "postgresql://u:p@127.0.0.1:5432/db",
        is_new=True,
    )
    meta = DbMetadataResponse(
        connection_name="pg",
        tables=[],
        cached_at=datetime.now(UTC),
    )
    sqlite_storage.save_metadata("pg", meta.model_dump_json(by_alias=True))

    FakeSession = _fake_llm_session_factory()
    frag = "email, display_name, created_at FROM public.users"
    body = json.dumps(
        {"choices": [{"message": {"content": frag}}]}
    )

    async def fake_get_session(_settings: object) -> FakeSession:
        return FakeSession(body)

    monkeypatch.setattr(llm_mod, "_get_aio_session", fake_get_session)

    try:
        out = await generate_select_sql("pg", "查询所有用户")
        assert out.strip().upper().startswith("SELECT")
        assert "FROM public.users" in out
    finally:
        await llm_mod.close_openai_client()


@pytest.mark.asyncio
async def test_generate_select_sql_rejects_bad_sql_from_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DB_QUERY_PATH", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    sqlite_storage.configure(tmp_path / "db_query.db")
    sqlite_storage.init_db()
    sqlite_storage.upsert_connection(
        "pg",
        "postgresql://u:p@127.0.0.1:5432/db",
        is_new=True,
    )
    meta = DbMetadataResponse(
        connection_name="pg",
        tables=[],
        cached_at=datetime.now(UTC),
    )
    sqlite_storage.save_metadata("pg", meta.model_dump_json(by_alias=True))

    FakeSession = _fake_llm_session_factory()
    body = '{"choices":[{"message":{"content":"DROP TABLE x"}}]}'

    async def fake_get_session(_settings: object) -> FakeSession:
        return FakeSession(body)

    monkeypatch.setattr(llm_mod, "_get_aio_session", fake_get_session)

    try:
        with pytest.raises(NaturalQueryUnusableError):
            await generate_select_sql("pg", "evil")
    finally:
        await llm_mod.close_openai_client()
