from __future__ import annotations

import asyncio
import json
import re
import socket
from typing import Any

import aiohttp
from aiohttp.abc import AbstractResolver, ResolveResult
from sqlglot import exp

from app.core.config import Settings, get_settings
from app.models.metadata import DbMetadataResponse
from app.services.connection import detect_db_type
from app.services.metadata import parse_cached_metadata
from app.services.sql_select import parse_single_select_statement
from app.storage import sqlite as sqlite_storage

# Sync socket.getaddrinfo: no asyncio thread pool, no aiodns/pycares threads (Toolbox nproc).
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
                    "host": str(ip),
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

    def __init__(self, detail: str | None = None) -> None:
        cleaned = _strip_terminal_noise(detail) if detail else None
        self.detail = cleaned or None
        super().__init__("natural_query_unusable")


class LlmUnavailableError(Exception):
    """无密钥、网络、OpenAI API 错误等；public_detail 可安全返回给客户端（勿含密钥）。"""

    def __init__(self, public_detail: str | None = None) -> None:
        self.public_detail = public_detail
        super().__init__("llm_unavailable")


def _safe_exc(e: BaseException, *, max_len: int = 500) -> str:
    s = f"{type(e).__name__}: {e}"
    return s if len(s) <= max_len else f"{s[: max_len - 3]}..."


def _strip_terminal_noise(s: str) -> str:
    """Remove ANSI + broken Rich fragments so API/JSON clients do not show [4m-style junk."""
    if not s:
        return s
    out = re.sub(r"\x1b\[[0-9;]*m", "", s)
    out = re.sub(r"\[[0-9;]*m", "", out)
    return out.strip()


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


_LEADING_SELECT_OR_WITH = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


def _normalize_llm_select_fragment(sql: str) -> str:
    """Some models return `col1, col2 FROM t` without SELECT; sqlglot cannot tokenize that."""
    s = sql.strip()
    if not s:
        return s
    if _LEADING_SELECT_OR_WITH.match(s):
        return s
    if re.search(r"\bfrom\b", s, re.IGNORECASE):
        return f"SELECT {s}"
    return s


def _message_content_to_str(content: Any) -> str:
    """OpenAI-compatible message.content: string or list of {type,text} blocks (some gateways)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts).strip()
    return ""


def _extract_sql_candidates(text: str) -> list[str]:
    """When the model mixes English/Chinese with SQL, take snippets that look like real queries.

    Prefer the *last* ``SELECT`` occurrence: phrases like "select all users" must not win over
    ``SELECT * FROM ...`` later in the same line.
    """
    t = text.strip()
    if not t:
        return []
    out: list[str] = []
    if re.match(r"(?is)\s*with\b", t):
        m = re.search(r"(?is)\bwith\b[\s\S]+?(?:;|\Z)", t)
        if m:
            chunk = m.group(0).strip().rstrip(";").strip()
            if chunk and chunk not in out:
                out.append(chunk)
    starts = [m.start() for m in re.finditer(r"(?i)\bselect\b", t)]
    for start in reversed(starts):
        chunk = t[start:]
        if ";" in chunk:
            chunk = chunk.split(";")[0]
        chunk = chunk.strip()
        if chunk and chunk not in out:
            out.append(chunk)
    return out


def _validate_llm_columns_against_metadata(sql: str, meta: DbMetadataResponse, *, dialect: str = "postgres") -> None:
    """Reject obvious hallucinated column names for a single-table SELECT."""
    try:
        tree = parse_single_select_statement(sql, dialect=dialect)
    except ValueError:
        return
    if isinstance(tree, exp.With):
        return
    if not isinstance(tree, exp.Select):
        return
    tables = list(tree.find_all(exp.Table))
    if len(tables) != 1:
        return
    tbl = tables[0]
    has_explicit_schema = tbl.db is not None
    sch_raw = tbl.db if has_explicit_schema else "public"
    sch_name = sch_raw.name if isinstance(sch_raw, exp.Identifier) else str(sch_raw)
    t_raw = tbl.name
    tname = t_raw.name if isinstance(t_raw, exp.Identifier) else str(t_raw)
    allowed: set[str] = set()
    for ti in meta.tables:
        # Match by table name; if no explicit schema was given, match any schema
        if ti.table_name.casefold() == tname.casefold():
            if not has_explicit_schema or ti.schema_name.casefold() == sch_name.casefold():
                allowed = {c.name for c in ti.columns}
                break
    else:
        return
    allowed_l = {x.casefold() for x in allowed}
    for col in tree.expressions:
        if isinstance(col, exp.Star):
            continue
        if isinstance(col, exp.Alias):
            inner = col.this
        else:
            inner = col
        if isinstance(inner, exp.Column):
            cname = inner.name
            if not cname:
                continue
            if cname not in allowed and cname.casefold() not in allowed_l:
                sample = sorted(allowed, key=str.casefold)[:24]
                tail = " …" if len(allowed) > 24 else ""
                raise NaturalQueryUnusableError(
                    detail=(
                        f"Schema 中不存在列 {cname!r}；该表可用列：{sample}{tail}。"
                        "不确定时请使用 SELECT *。"
                    )
                )


def _coerce_llm_reply_to_select(raw: str) -> str:
    """Strip fences, try plain body then regex fallback; normalize + validate; raise with detail."""
    if not raw.strip():
        raise NaturalQueryUnusableError(detail="模型未返回文本内容（或 content 非字符串/数组）")

    candidates: list[str] = []
    stripped = _strip_code_fence(raw)
    if stripped:
        candidates.append(stripped)
    for fb in _extract_sql_candidates(raw):
        if fb not in candidates:
            candidates.append(fb)

    last_detail: str | None = None
    for cand in candidates:
        sql = _normalize_llm_select_fragment(cand.strip())
        if not sql:
            continue
        try:
            parse_single_select_statement(sql)
        except ValueError as e:
            last_detail = str(e)
            continue
        else:
            return sql
    raise NaturalQueryUnusableError(
        detail=last_detail or "未解析出可执行的 SELECT（模型可能只返回了说明文字）",
    )


def _validate_generated_select(sql: str, *, dialect: str = "postgres") -> None:
    """确保为单条 SELECT（与 execute 前校验一致，此处不追加 LIMIT）。"""
    try:
        parse_single_select_statement(sql, dialect=dialect)
    except ValueError as e:
        raise NaturalQueryUnusableError(detail=str(e)) from None


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
    return _message_content_to_str(content)


async def generate_select_sql(connection_name: str, user_prompt: str) -> str:
    row = sqlite_storage.get_metadata_row(connection_name)
    if row is None:
        msg = "metadata_not_found"
        raise LookupError(msg)

    # Detect database type from stored connection URL
    conn_row = sqlite_storage.get_connection(connection_name)
    dialect = "postgres"
    db_label = "PostgreSQL"
    if conn_row is not None:
        try:
            db_type = detect_db_type(conn_row["url"])
            if db_type == "mysql":
                dialect = "mysql"
                db_label = "MySQL"
        except ValueError:
            pass

    meta = parse_cached_metadata(row["metadata_json"])
    settings = get_settings()
    if not settings.openai_api_key:
        raise LlmUnavailableError(
            "未配置 OPENAI_API_KEY。请在 backend/.env 中设置，保存后 docker-compose up -d --force-recreate backend。"
        )

    meta_json = meta.model_dump_json(by_alias=True)
    system = (
        f"你是 {db_label} SQL 专家。下面 JSON 是数据库表结构（camelCase 字段名）。\n"
        "规则：\n"
        "1. 只输出一条完整 SELECT 语句，必须以 SELECT 或 WITH 开头；"
        "不要只输出列清单加 FROM（例如必须先写 SELECT 列名... FROM ...）。"
        '不要写英文/中文说明句（例如不要写 "select all users ..." 这类话）；不要 Markdown、不要解释。\n'
        f"2. 使用标准 {db_label} 语法。\n"
        "3. 列名与表名必须严格来自下方 Schema JSON 的 tables[].columns[].name 与 "
        "schema_name/table_name；禁止臆造列名（例如未在 JSON 中出现则不得使用 username、"
        'name 等"常见"字段名）。若用户未指定列名或你不确定应选哪些列，请使用 SELECT * '
        "（或 WITH 内仅引用 JSON 中存在的对象）。\n"
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
                    "API 返回空响应体（HTTP 200）。请检查 OPENAI_BASE_URL 是否指向正确的 "
                    "OpenAI 兼容接口、代理是否截断响应。"
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
    sql = _coerce_llm_reply_to_select(raw)
    _validate_llm_columns_against_metadata(sql, meta, dialect=dialect)
    return sql
