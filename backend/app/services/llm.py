from __future__ import annotations

import asyncio
import json
import socket
from typing import Any

import aiohttp
from aiohttp.abc import AbstractResolver, ResolveResult
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.config import Settings, get_settings
from app.services.metadata import parse_cached_metadata
from app.storage import sqlite as sqlite_storage

# Sync socket.getaddrinfo in resolver hook: no asyncio thread pool, no aiodns/pycares background threads (Toolbox nproc).
LLM_HTTP_TRANSPORT = "aiohttp"
LLM_DNS_RESOLVER = "socket_sync"


def _is_ipv4_literal(host: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, host)
        return True
    except OSError:
        return False


def _is_ipv6_literal(host: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except OSError:
        return False


class _SyncSocketResolver(AbstractResolver):
    """Blocking getaddrinfo inside async resolve(); blocks the loop briefly but creates no Python threads."""

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        del family
        if _is_ipv4_literal(host) or _is_ipv6_literal(host):
            fam = socket.AF_INET6 if ":" in host else socket.AF_INET
            return [
                {
                    "hostname": host,
                    "host": host,
                    "port": port,
                    "family": fam,
                    "proto": socket.IPPROTO_TCP,
                    "flags": socket.AI_NUMERICHOST,
                }
            ]
        infos = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        if not infos:
            msg = f"nodename nor servname provided, or not known: {host!r}"
            raise OSError(msg)
        out: list[ResolveResult] = []
        for fam, _socktype, proto, _canon, sockaddr in infos:
            if fam == socket.AF_INET:
                ip, p = sockaddr[0], sockaddr[1]
            elif fam == socket.AF_INET6:
                ip, p = sockaddr[0], sockaddr[1]
            else:
                continue
            out.append(
                {
                    "hostname": host,
                    "host": ip,
                    "port": int(p),
                    "family": fam,
                    "proto": int(proto),
                    "flags": socket.AI_NUMERICHOST,
                }
            )
        if not out:
            msg = f"No TCP address resolved for {host!r}"
            raise OSError(msg)
        return out

    async def close(self) -> None:
        return None
_HTTP_LOCK = asyncio.Lock()
_aio_session: aiohttp.ClientSession | None = None
_aio_session_key: tuple[str, str | None] | None = None


def _openai_cache_key(settings: Settings) -> tuple[str, str | None]:
    return (settings.openai_api_key or "", settings.openai_base_url)


def _api_base(settings: Settings) -> str:
    """OpenAI-compatible base; must end with /v1 for official API (root host serves HTML)."""
    base = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
    if base.casefold() in ("https://api.openai.com", "http://api.openai.com"):
        return "https://api.openai.com/v1"
    return base


async def _get_aio_session(settings: Settings) -> aiohttp.ClientSession:
    global _aio_session, _aio_session_key
    key = _openai_cache_key(settings)
    async with _HTTP_LOCK:
        if _aio_session is not None and _aio_session_key == key:
            return _aio_session
        if _aio_session is not None:
            await _aio_session.close()
            _aio_session = None
            _aio_session_key = None
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(
            limit=4,
            limit_per_host=2,
            resolver=_SyncSocketResolver(),
        )
        _aio_session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            raise_for_status=False,
        )
        _aio_session_key = key
        return _aio_session


async def close_openai_client() -> None:
    global _aio_session, _aio_session_key
    async with _HTTP_LOCK:
        if _aio_session is not None:
            await _aio_session.close()
            _aio_session = None
            _aio_session_key = None


class NaturalQueryUnusableError(Exception):
    """LLM 输出为空、无法解析为单条 SELECT，或语义不可用。"""


class LlmUnavailableError(Exception):
    """无密钥、网络、OpenAI API 错误等；public_detail 可安全返回给客户端（勿含密钥）。"""

    def __init__(self, public_detail: str | None = None) -> None:
        self.public_detail = public_detail
        super().__init__("llm_unavailable")


def _safe_exc(e: BaseException, *, max_len: int = 500) -> str:
    s = f"{type(e).__name__}: {e}"
    return s if len(s) <= max_len else f"{s[: max_len - 3]}..."


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _validate_generated_select(sql: str) -> None:
    """确保为单条 PostgreSQL SELECT（与 execute 前校验一致，此处不追加 LIMIT）。"""
    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except ParseError:
        raise NaturalQueryUnusableError() from None
    if len(statements) != 1:
        raise NaturalQueryUnusableError()
    stmt = statements[0]
    if isinstance(stmt, exp.Union):
        raise NaturalQueryUnusableError()
    if not isinstance(stmt, (exp.Select, exp.With)):
        raise NaturalQueryUnusableError()


def _format_upstream_http_error(status: int, body_text: str) -> str:
    """Readable detail for OpenAI-style error JSON from upstream (incl. third-party gateways)."""
    head = f"上游 HTTP {status}"
    if not (body_text or "").strip():
        return f"{head}（无响应正文）"
    try:
        j = json.loads(body_text)
    except json.JSONDecodeError:
        return f"{head} | {body_text.strip()[:500]}"
    err = j.get("error")
    parts: list[str] = [head]
    hint = ""
    if isinstance(err, dict):
        if err.get("type"):
            parts.append(str(err["type"]))
        if err.get("message") is not None:
            m = str(err["message"])
            if len(m) > 320:
                m = m[:317] + "..."
            parts.append(m)
        if err.get("type") == "bad_response_status_code" or err.get("message") == "openai_error":
            hint = (
                " [网关转发上游失败较常见：核对密钥/额度、OPENAI_MODEL 与文档，或联系网关方]"
            )
    elif isinstance(err, str):
        parts.append(err[:400])
    else:
        return f"{head} | {body_text.strip()[:500]}"
    return " | ".join(parts) + hint


def _parse_chat_content(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise LlmUnavailableError("OpenAI 响应中无 choices 内容")
    first = choices[0]
    if not isinstance(first, dict):
        raise LlmUnavailableError("OpenAI 响应格式异常")
    msg = first.get("message")
    if not isinstance(msg, dict):
        raise LlmUnavailableError("OpenAI 响应中无 message")
    content = msg.get("content")
    return (content or "").strip() if isinstance(content, str) else ""


async def generate_select_sql(connection_name: str, user_prompt: str) -> str:
    row = sqlite_storage.get_metadata_row(connection_name)
    if row is None:
        msg = "metadata_not_found"
        raise LookupError(msg)

    meta = parse_cached_metadata(row["metadata_json"])
    settings = get_settings()
    if not settings.openai_api_key:
        raise LlmUnavailableError(
            "未配置 OPENAI_API_KEY。请在 backend/.env 中设置，保存后 docker-compose up -d --force-recreate backend。"
        )

    meta_json = meta.model_dump_json(by_alias=True)
    system = (
        "你是 PostgreSQL SQL 专家。下面 JSON 是数据库表结构（camelCase 字段名）。\n"
        "规则：\n"
        "1. 只输出一条 SELECT 语句，不要 Markdown、不要解释。\n"
        "2. 使用标准 PostgreSQL 语法。\n"
        f"\nSchema JSON:\n{meta_json}"
    )

    session = await _get_aio_session(settings)
    url = f"{_api_base(settings)}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt.strip()},
        ],
        "temperature": 0,
    }

    try:
        async with session.post(url, headers=headers, json=payload) as resp:
            body_text = await resp.text()
            if resp.status >= 400:
                raise LlmUnavailableError(_format_upstream_http_error(resp.status, body_text))
            stripped = (body_text or "").strip()
            if stripped.startswith("\ufeff"):
                stripped = stripped[1:].strip()
            if not stripped:
                raise LlmUnavailableError(
                    "API 返回空响应体（HTTP 200）。请检查 OPENAI_BASE_URL 是否指向正确的 OpenAI 兼容接口、代理是否截断响应。"
                )
            if stripped.lstrip().startswith("<"):
                raise LlmUnavailableError(
                    "API 返回了 HTML 页面而非 JSON（常见为官网、登录页、404 或反代错误页）。"
                    "请对照服务商文档核对 OPENAI_BASE_URL：须为 OpenAI 兼容网关，且实际可访问 "
                    "「Base + /chat/completions」；密钥与该网关须为同一套。"
                )
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as e:
                preview = stripped[:300].replace("\n", " ")
                raise LlmUnavailableError(
                    f"API 响应不是合法 JSON（{type(e).__name__}）。"
                    f"请确认 OPENAI_BASE_URL 与密钥对应同一服务商。响应开头: {preview!r}"
                ) from e
    except LlmUnavailableError:
        raise
    except aiohttp.ClientError as e:
        raise LlmUnavailableError(_safe_exc(e)) from e
    except Exception as e:
        raise LlmUnavailableError(_safe_exc(e)) from e

    raw = _parse_chat_content(data)
    if not raw:
        raise NaturalQueryUnusableError()

    sql = _strip_code_fence(raw)
    if not sql:
        raise NaturalQueryUnusableError()
    _validate_generated_select(sql)
    return sql
