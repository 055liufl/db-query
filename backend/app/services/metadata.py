from __future__ import annotations

from datetime import UTC, datetime

import asyncpg

from app.models.metadata import ColumnInfo, DbMetadataResponse, TableInfo


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


def parse_cached_metadata(metadata_json: str) -> DbMetadataResponse:
    return DbMetadataResponse.model_validate_json(metadata_json)
