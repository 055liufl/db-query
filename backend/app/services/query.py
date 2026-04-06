from __future__ import annotations

import math
import time
from decimal import Decimal
from typing import Any, cast

import asyncpg
from sqlglot import exp

from app.models.query import QueryColumn, QueryResult
from app.services.sql_select import parse_single_select_statement


def _json_safe_cell(value: Any) -> Any:
    """Starlette JSONResponse uses allow_nan=False; FastAPI Decimal encoder can emit float nan."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, Decimal):
        if value.is_nan() or value.is_infinite():
            return None
        return value
    return value


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _json_safe_cell(v) for k, v in row.items()}


def _apply_limit_if_missing(stmt: exp.Expression, limit: int) -> exp.Expression:
    if isinstance(stmt, exp.Select):
        if stmt.args.get("limit") is None:
            return stmt.limit(limit)
        return stmt
    if isinstance(stmt, exp.With):
        inner = stmt.this
        if isinstance(inner, exp.Select) and inner.args.get("limit") is None:
            # sqlglot With.replace signature not fully typed for nested Select
            return cast(exp.Expression, stmt.replace(inner, inner.limit(limit)))  # type: ignore[call-arg]
        return stmt
    return stmt


def _limit_was_missing(stmt: exp.Expression) -> bool:
    if isinstance(stmt, exp.Select):
        return stmt.args.get("limit") is None
    if isinstance(stmt, exp.With):
        inner = stmt.this
        if isinstance(inner, exp.Select):
            return inner.args.get("limit") is None
    return True


def validate_and_prepare_sql(sql: str) -> tuple[str, bool]:
    stmt = parse_single_select_statement(sql)
    missing = _limit_was_missing(stmt)
    final_stmt = _apply_limit_if_missing(stmt, 1000) if missing else stmt
    final_sql = final_stmt.sql(dialect="postgres")
    return final_sql, missing


def _column_name_and_oid(attr: Any) -> tuple[str, int]:
    """asyncpg Attribute is a NamedTuple, so isinstance(attr, tuple) is true; a[1] is Type, not oid."""
    t = getattr(attr, "type", None)
    if t is not None and hasattr(t, "oid"):
        return str(attr.name), int(t.oid)
    if isinstance(attr, tuple) and len(attr) >= 2:
        second = attr[1]
        if hasattr(second, "oid"):
            return str(attr[0]), int(second.oid)
        return str(attr[0]), int(second)
    msg = f"unexpected column attribute: {attr!r}"
    raise TypeError(msg)


async def _typenames_for_oids(conn: asyncpg.Connection, oids: list[int]) -> dict[int, str]:
    if not oids:
        return {}
    unique = list({oid for oid in oids})
    rows = await conn.fetch(
        "SELECT oid, typname FROM pg_type WHERE oid = ANY($1::oid[])",
        unique,
    )
    return {int(r["oid"]): str(r["typname"]) for r in rows}


async def execute_select(url: str, sql: str) -> QueryResult:
    final_sql, limit_added = validate_and_prepare_sql(sql)
    started = time.perf_counter()
    conn = await asyncpg.connect(dsn=url, timeout=30.0)
    try:
        stmt = await conn.prepare(final_sql)
        raw_attrs = stmt.get_attributes()
        names: list[str] = []
        oids: list[int] = []
        for a in raw_attrs:
            n, oid = _column_name_and_oid(a)
            names.append(n)
            oids.append(oid)
        oid_map = await _typenames_for_oids(conn, oids)
        columns = [
            QueryColumn(name=n, data_type=oid_map.get(oid, "unknown"))
            for n, oid in zip(names, oids, strict=False)
        ]
        records = await stmt.fetch()
        rows_out: list[dict[str, Any]] = [_json_safe_row(dict(r)) for r in records]
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        row_count = len(rows_out)
        truncated = bool(limit_added and row_count >= 1000)
        return QueryResult(
            sql=final_sql,
            columns=columns,
            rows=rows_out,
            row_count=row_count,
            truncated=truncated,
            elapsed_ms=elapsed_ms,
        )
    finally:
        await conn.close()
