from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_db_path: Path | None = None
_lock = threading.Lock()


def configure(db_file: Path) -> None:
    global _db_path
    _db_path = db_file


def _require_path() -> Path:
    if _db_path is None:
        msg = "SQLite not configured"
        raise RuntimeError(msg)
    return _db_path


def init_db() -> None:
    """Stdlib sqlite3 only (no background threads). Required for tiny Docker Toolbox VMs."""
    path = _require_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
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
        )
        conn.commit()
    finally:
        conn.close()


def connection_exists(name: str) -> bool:
    path = _require_path()
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute(
            "SELECT 1 FROM db_connections WHERE name = ? LIMIT 1",
            (name,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def upsert_connection(name: str, url: str, *, is_new: bool) -> dict[str, Any]:
    path = _require_path()
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with _lock:
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            if is_new:
                conn.execute(
                    """
                    INSERT INTO db_connections (name, url, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, url, now, now),
                )
            else:
                conn.execute(
                    """
                    UPDATE db_connections
                    SET url = ?, updated_at = ?
                    WHERE name = ?
                    """,
                    (url, now, name),
                )
            conn.commit()
        finally:
            conn.close()
    result = get_connection(name)
    if result is None:
        msg = "upsert failed"
        raise RuntimeError(msg)
    return result


def get_connection(name: str) -> dict[str, Any] | None:
    path = _require_path()
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT name, url, created_at, updated_at FROM db_connections WHERE name = ?",
            (name,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_connections() -> list[dict[str, Any]]:
    path = _require_path()
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT name, url, created_at, updated_at FROM db_connections ORDER BY name ASC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_metadata_row(connection_name: str) -> dict[str, Any] | None:
    path = _require_path()
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT connection_name, metadata_json, cached_at
            FROM db_metadata
            WHERE connection_name = ?
            """,
            (connection_name,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_metadata(connection_name: str, metadata_json: str) -> None:
    path = _require_path()
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with _lock:
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                INSERT INTO db_metadata (connection_name, metadata_json, cached_at)
                VALUES (?, ?, ?)
                ON CONFLICT(connection_name) DO UPDATE SET
                    metadata_json = excluded.metadata_json,
                    cached_at = excluded.cached_at
                """,
                (connection_name, metadata_json, now),
            )
            conn.commit()
        finally:
            conn.close()


def delete_connection(name: str) -> bool:
    """Remove connection row; db_metadata cascades (ON DELETE CASCADE)."""
    path = _require_path()
    with _lock:
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.execute("DELETE FROM db_connections WHERE name = ?", (name,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def delete_metadata(connection_name: str) -> None:
    path = _require_path()
    with _lock:
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                "DELETE FROM db_metadata WHERE connection_name = ?",
                (connection_name,),
            )
            conn.commit()
        finally:
            conn.close()
