from __future__ import annotations

import re

import asyncpg

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def validate_connection_name(name: str) -> None:
    if not _NAME_RE.match(name):
        msg = "连接名称仅允许字母、数字、连字符、下划线，长度 1~64"
        raise ValueError(msg)


def validate_postgres_url(url: str) -> None:
    u = url.strip()
    if not u.startswith(("postgres://", "postgresql://")):
        msg = "连接 URL 格式不正确，必须以 postgres:// 或 postgresql:// 开头"
        raise ValueError(msg)


async def test_postgres_connection(url: str, *, timeout_s: float = 30.0) -> None:
    conn = await asyncpg.connect(dsn=url, timeout=timeout_s)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()
