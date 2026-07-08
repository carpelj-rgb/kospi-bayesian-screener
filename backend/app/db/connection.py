from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS universe_snapshots (
    snapshot_date TEXT NOT NULL,
    market TEXT NOT NULL,
    tickers_json TEXT NOT NULL,
    used_fallback INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, market)
);

CREATE TABLE IF NOT EXISTS factor_snapshots (
    snapshot_date TEXT NOT NULL,
    market TEXT NOT NULL,
    tickers_key TEXT NOT NULL,
    as_of TEXT NOT NULL,
    frame_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, market, tickers_key)
);
"""


def resolve_sqlite_path() -> Path:
    configured = Path(settings.sqlite_path)
    if configured.is_absolute():
        return configured
    backend_root = Path(__file__).resolve().parent.parent.parent
    return backend_root / configured


def init_database() -> Path:
    db_path = resolve_sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()
    return db_path


def get_connection() -> sqlite3.Connection:
    db_path = resolve_sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
