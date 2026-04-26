from __future__ import annotations

from datetime import UTC, datetime

import asyncpg
import aiomysql

from app.models.metadata import ColumnInfo, DbMetadataResponse, TableInfo
from app.services.connection import _parse_mysql_url, detect_db_type


async def fetch_metadata_from_postgres(url: str, *, timeout_s: float = 30.0) -> DbMetadataResponse:
    conn = await asyncpg.connect(dsn=url, timeout=timeout_s)
    try:
        table_rows = await conn.fetch(
            """
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_type IN ('BASE TABLE', 'VIEW')
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
            """
        )
        tables: list[TableInfo] = []
        for tr in table_rows:
            schema = tr["table_schema"]
            tname = tr["table_name"]
            ttype = tr["table_type"]
            col_rows = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """,
                schema,
                tname,
            )
            columns = [
                ColumnInfo(
                    name=c["column_name"],
                    data_type=c["data_type"],
                    is_nullable=c["is_nullable"] == "YES",
                    column_default=c["column_default"],
                )
                for c in col_rows
            ]
            tables.append(
                TableInfo(
                    schema_name=schema,
                    table_name=tname,
                    table_type=ttype,
                    columns=columns,
                )
            )
        cached_at = datetime.now(UTC)
        return DbMetadataResponse(connection_name="", tables=tables, cached_at=cached_at)
    finally:
        await conn.close()


async def fetch_metadata_from_mysql(url: str, *, timeout_s: float = 30.0) -> DbMetadataResponse:
    params = _parse_mysql_url(url)
    db_name = params.get("db")
    conn = await aiomysql.connect(
        **params,
        connect_timeout=int(timeout_s),
    )
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Build WHERE clause for database filtering
            if db_name:
                await cur.execute(
                    "SELECT table_schema, table_name, table_type "
                    "FROM information_schema.tables "
                    "WHERE table_schema = %s "
                    "AND table_type IN ('BASE TABLE', 'VIEW') "
                    "ORDER BY table_schema, table_name",
                    (db_name,),
                )
            else:
                await cur.execute(
                    "SELECT table_schema, table_name, table_type "
                    "FROM information_schema.tables "
                    "WHERE table_schema NOT IN "
                    "('information_schema', 'mysql', 'performance_schema', 'sys') "
                    "AND table_type IN ('BASE TABLE', 'VIEW') "
                    "ORDER BY table_schema, table_name"
                )
            table_rows = await cur.fetchall()

            tables: list[TableInfo] = []
            for tr in table_rows:
                # aiomysql DictCursor returns lowercase keys for information_schema queries
                tr_lower = {k.lower(): v for k, v in tr.items()}
                schema = tr_lower["table_schema"]
                tname = tr_lower["table_name"]
                ttype = tr_lower["table_type"]

                await cur.execute(
                    "SELECT column_name, data_type, is_nullable, column_default "
                    "FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s "
                    "ORDER BY ordinal_position",
                    (schema, tname),
                )
                col_rows = await cur.fetchall()

                columns = []
                for c in col_rows:
                    cl = {k.lower(): v for k, v in c.items()}
                    columns.append(ColumnInfo(
                        name=cl.get("column_name", ""),
                        data_type=cl.get("data_type", ""),
                        is_nullable=cl.get("is_nullable", "NO") == "YES",
                        column_default=cl.get("column_default"),
                    ))
                tables.append(
                    TableInfo(
                        schema_name=schema,
                        table_name=tname,
                        table_type=ttype,
                        columns=columns,
                    )
                )
        cached_at = datetime.now(UTC)
        return DbMetadataResponse(connection_name="", tables=tables, cached_at=cached_at)
    finally:
        conn.ensure_closed()


async def fetch_metadata(url: str, *, timeout_s: float = 30.0) -> DbMetadataResponse:
    """Dispatch to the correct metadata fetcher based on URL scheme."""
    db_type = detect_db_type(url)
    if db_type == "postgres":
        return await fetch_metadata_from_postgres(url, timeout_s=timeout_s)
    return await fetch_metadata_from_mysql(url, timeout_s=timeout_s)


def parse_cached_metadata(metadata_json: str) -> DbMetadataResponse:
    return DbMetadataResponse.model_validate_json(metadata_json)
