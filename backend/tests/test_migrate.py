from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.migrate import apply_sqlite_migrations


def test_migrations_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        apply_sqlite_migrations(conn)
        apply_sqlite_migrations(conn)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        )
        names = {r[0] for r in cur.fetchall()}
        assert "db_connections" in names
        assert "db_metadata" in names
        assert "schema_migrations" in names
        cur = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
        assert [r[0] for r in cur.fetchall()] == [1]
    finally:
        conn.close()
