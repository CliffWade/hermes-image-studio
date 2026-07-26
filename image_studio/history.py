"""Generation history tracker for Hermes Image Studio.

Lightweight SQLite store that records every generation and upscale
operation. Supports browsing, re-generation with tweaked prompts,
and pruning old entries.

The database file lives alongside generated images by default
(~/.hermes/data/image-studio/history.db) but is configurable.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

_HOME = os.path.expanduser("~/.hermes/data/image-studio")


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _db_path() -> str:
    return os.path.join(_ensure_dir(_HOME), "history.db")


# ---------------------------------------------------------------------------
# Thread-safe connection
# ---------------------------------------------------------------------------

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local connection (each thread gets its own cursor-safe conn)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        path = _db_path()
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        _init_schema(conn)
        _local.conn = conn
    return _local.conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            prompt      TEXT NOT NULL,
            preset      TEXT,
            model       TEXT NOT NULL,
            seed        INTEGER,
            steps       INTEGER,
            aspect_ratio TEXT,
            width       INTEGER,
            height      INTEGER,
            image_url   TEXT,
            file_path   TEXT,
            tags        TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS upscales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            source_image_url TEXT NOT NULL,
            result_image_url TEXT,
            scale           INTEGER NOT NULL DEFAULT 2,
            source_gen_id   INTEGER REFERENCES generations(id)
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Record keeping
# ---------------------------------------------------------------------------


def record_generation(
    prompt: str,
    *,
    preset: Optional[str] = None,
    model: str = "flux-pro",
    seed: int = -1,
    steps: int = 28,
    aspect_ratio: str = "landscape",
    width: int = 1344,
    height: int = 768,
    image_url: str = "",
    file_path: str = "",
    tags: str = "",
) -> int:
    """Insert a generation record and return its ID."""
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO generations
           (prompt, preset, model, seed, steps, aspect_ratio, width, height,
            image_url, file_path, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (prompt, preset, model, seed, steps, aspect_ratio,
         width, height, image_url, file_path, tags or ""),
    )
    conn.commit()
    return cur.lastrowid


def record_upscale(
    source_image_url: str,
    result_image_url: str,
    *,
    scale: int = 2,
    source_gen_id: Optional[int] = None,
) -> int:
    """Insert an upscale record and return its ID."""
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO upscales
           (source_image_url, result_image_url, scale, source_gen_id)
           VALUES (?, ?, ?, ?)""",
        (source_image_url, result_image_url, scale, source_gen_id),
    )
    conn.commit()
    return cur.lastrowid


def recent_generations(limit: int = 10) -> List[Dict[str, Any]]:
    """Return the most recent N generations."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM generations ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_generation(gen_id: int) -> Optional[Dict[str, Any]]:
    """Get a single generation by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM generations WHERE id = ?", (gen_id,)
    ).fetchone()
    return dict(row) if row else None


def count_generations() -> int:
    """Total generations recorded."""
    conn = _get_conn()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM generations").fetchone()
    return row["cnt"] if row else 0


def prune_older_than(days: int = 90) -> int:
    """Remove generations older than N days. Returns count removed."""
    conn = _get_conn()
    cur = conn.execute(
        "DELETE FROM generations WHERE created_at < datetime('now', ?)",
        (f"-{days} days",),
    )
    removed = cur.rowcount
    conn.commit()
    return removed
