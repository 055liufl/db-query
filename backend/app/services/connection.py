from __future__ import annotations

import re
from urllib.parse import urlparse

import asyncpg
import aiomysql


_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def validate_connection_name(name: str) -> None:
    if not _NAME_RE.match(name):
        msg = "连接名称仅允许字母、数字、连字符、下划线，长度 1~64"
        raise ValueError(msg)


def detect_db_type(url: str) -> str:
    """Return 'postgres' or 'mysql' based on URL scheme."""
    u = url.strip()
    if u.startswith(("postgres://", "postgresql://")):
        return "postgres"
    if u.startswith("mysql://"):
        return "mysql"
    msg = "连接 URL 格式不正确，必须以 postgres://、postgresql:// 或 mysql:// 开头"
    raise ValueError(msg)


def validate_postgres_url(url: str) -> None:
    u = url.strip()
    if not u.startswith(("postgres://", "postgresql://")):
        msg = "连接 URL 格式不正确，必须以 postgres:// 或 postgresql:// 开头"
        raise ValueError(msg)


def validate_db_url(url: str) -> str:
    """Validate and return the db type ('postgres' or 'mysql')."""
    return detect_db_type(url)


def _parse_mysql_url(url: str) -> dict:
    """Parse mysql://user:pass@host:port/db into connection kwargs."""
    parsed = urlparse(url.strip())
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "db": parsed.path.lstrip("/") or None,
        "charset": "utf8mb4",
    }


async def test_postgres_connection(url: str, *, timeout_s: float = 30.0) -> None:
    conn = await asyncpg.connect(dsn=url, timeout=timeout_s)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()


async def test_mysql_connection(url: str, *, timeout_s: float = 30.0) -> None:
    params = _parse_mysql_url(url)
    conn = await aiomysql.connect(
        **params,
        connect_timeout=int(timeout_s),
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
    finally:
        conn.ensure_closed()


async def test_connection(url: str, *, timeout_s: float = 30.0) -> None:
    """Test connection for any supported database type."""
    db_type = detect_db_type(url)
    if db_type == "postgres":
        await test_postgres_connection(url, timeout_s=timeout_s)
    else:
        await test_mysql_connection(url, timeout_s=timeout_s)
