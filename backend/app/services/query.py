from __future__ import annotations

import math
import time
from decimal import Decimal
from typing import Any, cast

import asyncpg
import aiomysql
from sqlglot import exp

from app.models.query import QueryColumn, QueryResult
from app.services.connection import _parse_mysql_url, detect_db_type
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


def validate_and_prepare_sql(sql: str, *, dialect: str = "postgres") -> tuple[str, bool]:
    stmt = parse_single_select_statement(sql, dialect=dialect)
    missing = _limit_was_missing(stmt)
    final_stmt = _apply_limit_if_missing(stmt, 1000) if missing else stmt
    final_sql = final_stmt.sql(dialect=dialect)
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


async def _execute_select_postgres(url: str, sql: str) -> QueryResult:
    final_sql, limit_added = validate_and_prepare_sql(sql, dialect="postgres")
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


async def _execute_select_mysql(url: str, sql: str) -> QueryResult:
    final_sql, limit_added = validate_and_prepare_sql(sql, dialect="mysql")
    params = _parse_mysql_url(url)
    started = time.perf_counter()
    conn = await aiomysql.connect(**params, connect_timeout=30)
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(final_sql)
            records = await cur.fetchall()
            # Extract column metadata from cursor.description
            columns: list[QueryColumn] = []
            if cur.description:
                for desc in cur.description:
                    col_name = desc[0]
                    # desc[1] is the type_code from MySQL; map to a readable name
                    type_code = desc[1]
                    type_name = _mysql_type_name(type_code)
                    columns.append(QueryColumn(name=col_name, data_type=type_name))

            rows_out: list[dict[str, Any]] = [_json_safe_row(r) for r in records]
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
        conn.close()


# MySQL field type constants (from pymysql/constants/FIELD_TYPE.py)
_MYSQL_TYPE_MAP: dict[int, str] = {
    0: "decimal",
    1: "tinyint",
    2: "smallint",
    3: "int",
    4: "float",
    5: "double",
    6: "null",
    7: "timestamp",
    8: "bigint",
    9: "mediumint",
    10: "date",
    11: "time",
    12: "datetime",
    13: "year",
    14: "newdate",
    15: "varchar",
    16: "bit",
    245: "json",
    246: "newdecimal",
    247: "enum",
    248: "set",
    249: "tinyblob",
    250: "mediumblob",
    251: "longblob",
    252: "blob",
    253: "varchar",
    254: "char",
    255: "geometry",
}


def _mysql_type_name(type_code: int) -> str:
    return _MYSQL_TYPE_MAP.get(type_code, "unknown")


async def execute_select(url: str, sql: str) -> QueryResult:
    """Dispatch to the correct query executor based on URL scheme."""
    db_type = detect_db_type(url)
    if db_type == "postgres":
        return await _execute_select_postgres(url, sql)
    return await _execute_select_mysql(url, sql)
