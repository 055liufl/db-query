"""SQLite schema migrations: versioned DDL + `schema_migrations` 表（可重复执行的迁移链）。"""

from __future__ import annotations

import sqlite3

_DDL_V1 = """
CREATE TABLE IF NOT EXISTS db_connections (
    name TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS db_metadata (
    connection_name TEXT PRIMARY KEY,
    metadata_json TEXT NOT NULL,
    cached_at TEXT NOT NULL,
    FOREIGN KEY (connection_name) REFERENCES db_connections(name) ON DELETE CASCADE
);
"""

MIGRATIONS: list[tuple[int, str]] = [(1, _DDL_V1)]


def apply_sqlite_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY NOT NULL)",
    )
    conn.commit()
    for version, ddl in MIGRATIONS:
        cur = conn.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (version,))
        if cur.fetchone() is not None:
            continue
        conn.executescript(ddl)
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
