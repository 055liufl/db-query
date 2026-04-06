from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.config import Settings
from app.models.metadata import ColumnInfo, DbMetadataResponse, TableInfo
from app.services.llm import (
    NaturalQueryUnusableError,
    _api_base,
    _coerce_llm_reply_to_select,
    _format_upstream_http_error,
    _message_content_to_str,
    _strip_code_fence,
    _strip_terminal_noise,
    _validate_generated_select,
    _validate_llm_columns_against_metadata,
)


def test_api_base_default_is_openai_v1() -> None:
    s = Settings(
        openai_api_key="k",
        openai_base_url=None,
        openai_model="gpt-4o-mini",
    )
    assert _api_base(s) == "https://api.openai.com/v1"


def test_api_base_fixes_openai_root_host() -> None:
    s = Settings(
        openai_api_key="k",
        openai_base_url="https://api.openai.com",
        openai_model="gpt-4o-mini",
    )
    assert _api_base(s) == "https://api.openai.com/v1"


def test_api_base_preserves_custom_gateway() -> None:
    s = Settings(
        openai_api_key="k",
        openai_base_url="https://gateway.example/v1",
        openai_model="gpt-4o-mini",
    )
    assert _api_base(s) == "https://gateway.example/v1"


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("SELECT 1", "SELECT 1"),
        ("```sql\nSELECT 1\n```", "SELECT 1"),
        ("```\nSELECT 2\n```", "SELECT 2"),
    ],
)
def test_strip_code_fence(text: str, want: str) -> None:
    assert _strip_code_fence(text) == want


def test_validate_generated_select_ok() -> None:
    _validate_generated_select("SELECT id FROM users")


def _sample_metadata() -> DbMetadataResponse:
    return DbMetadataResponse(
        connection_name="x",
        tables=[
            TableInfo(
                schema_name="public",
                table_name="users",
                table_type="BASE TABLE",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_nullable=True),
                    ColumnInfo(name="email", data_type="text", is_nullable=True),
                ],
            )
        ],
        cached_at=datetime.now(UTC),
    )


def test_validate_llm_columns_rejects_unknown_column() -> None:
    meta = _sample_metadata()
    with pytest.raises(NaturalQueryUnusableError) as exc:
        _validate_llm_columns_against_metadata("SELECT id, username FROM public.users", meta)
    assert exc.value.detail and "username" in exc.value.detail


def test_validate_llm_columns_allows_star_and_known_columns() -> None:
    meta = _sample_metadata()
    _validate_llm_columns_against_metadata("SELECT * FROM public.users", meta)
    _validate_llm_columns_against_metadata("SELECT id, email FROM public.users", meta)


def test_validate_generated_select_rejects_insert() -> None:
    with pytest.raises(NaturalQueryUnusableError) as exc:
        _validate_generated_select("INSERT INTO t VALUES (1)")
    assert exc.value.detail is not None
    assert "SELECT" in exc.value.detail or "仅允许" in exc.value.detail


def test_message_content_to_str_accepts_openai_text_blocks() -> None:
    blocks = [{"type": "text", "text": "SELECT 1"}]
    assert _message_content_to_str(blocks) == "SELECT 1"


def test_coerce_llm_reply_extracts_sql_after_chinese() -> None:
    raw = "可以执行以下查询：\nSELECT id FROM public.users LIMIT 10;"
    assert _coerce_llm_reply_to_select(raw).strip().upper().startswith("SELECT")


def test_coerce_llm_reply_prefers_last_select_over_english_select_verb() -> None:
    raw = "select all users with schema is: SELECT * FROM public.users"
    out = _coerce_llm_reply_to_select(raw)
    assert out.strip().upper().startswith("SELECT")
    assert "FROM public.users" in out
    assert out.count("SELECT") == 1


def test_strip_terminal_noise_removes_ansi_and_bracket_codes() -> None:
    s = "a\x1b[4mb\x1b[0m c[4mwith[0m"
    assert _strip_terminal_noise(s) == "ab cwith"


def test_coerce_llm_reply_rejects_plain_chinese() -> None:
    raw = "请先在界面中选择数据库连接。"
    with pytest.raises(NaturalQueryUnusableError) as exc:
        _coerce_llm_reply_to_select(raw)
    assert exc.value.detail is not None


def test_format_upstream_http_error_empty_body() -> None:
    assert "无响应正文" in _format_upstream_http_error(502, "")


def test_format_upstream_http_error_parses_openai_style_json() -> None:
    body = '{"error":{"message":"nope","type":"invalid_request_error"}}'
    out = _format_upstream_http_error(400, body)
    assert "上游 HTTP 400" in out
    assert "invalid_request_error" in out
    assert "nope" in out


def test_format_upstream_http_error_bad_response_hint() -> None:
    body = '{"error":{"message":"openai_error","type":"bad_response_status_code"}}'
    out = _format_upstream_http_error(400, body)
    assert "bad_response_status_code" in out
    assert "网关" in out
