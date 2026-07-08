from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from app.config import settings
from app.db.connection import get_connection, init_database
from app.db.serializers import (
    factor_frame_from_json,
    factor_frame_to_json,
    tickers_key,
    today_iso,
    utc_now_iso,
)

if TYPE_CHECKING:
    from app.factors.pipeline import FactorFrame

logger = logging.getLogger(__name__)


@dataclass
class UniverseSnapshot:
    tickers: list[str]
    used_fallback: bool


class SnapshotStore:
    def __init__(self) -> None:
        init_database()

    def load_universe(self, market: str, snapshot_date: date | None = None) -> UniverseSnapshot | None:
        if not settings.snapshot_enabled:
            return None
        day = today_iso(snapshot_date)
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT tickers_json, used_fallback
                FROM universe_snapshots
                WHERE snapshot_date = ? AND market = ?
                """,
                (day, market.upper()),
            ).fetchone()
        if row is None:
            return None
        tickers = json.loads(row["tickers_json"])
        if not isinstance(tickers, list) or not tickers:
            return None
        logger.debug("Universe snapshot hit: %s %s (%d tickers)", day, market, len(tickers))
        return UniverseSnapshot(
            tickers=[str(t) for t in tickers],
            used_fallback=bool(row["used_fallback"]),
        )

    def save_universe(
        self,
        market: str,
        tickers: list[str],
        used_fallback: bool,
        snapshot_date: date | None = None,
    ) -> None:
        if not settings.snapshot_enabled or not tickers:
            return
        day = today_iso(snapshot_date)
        payload = json.dumps(tickers, ensure_ascii=False)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO universe_snapshots (
                    snapshot_date, market, tickers_json, used_fallback, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_date, market) DO UPDATE SET
                    tickers_json = excluded.tickers_json,
                    used_fallback = excluded.used_fallback,
                    created_at = excluded.created_at
                """,
                (day, market.upper(), payload, int(used_fallback), utc_now_iso()),
            )
            conn.commit()
        logger.info("Saved universe snapshot: %s %s (%d tickers)", day, market, len(tickers))

    def load_factor_frame(
        self,
        market: str,
        tickers: list[str],
        snapshot_date: date | None = None,
    ) -> FactorFrame | None:
        if not settings.snapshot_enabled or not tickers:
            return None
        day = today_iso(snapshot_date)
        key = tickers_key(tickers)
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT frame_json
                FROM factor_snapshots
                WHERE snapshot_date = ? AND market = ? AND tickers_key = ?
                """,
                (day, market.upper(), key),
            ).fetchone()
        if row is None:
            return None
        try:
            frame = factor_frame_from_json(row["frame_json"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning("Corrupt factor snapshot ignored: %s %s", day, market)
            return None
        logger.debug("Factor snapshot hit: %s %s (%d tickers)", day, market, len(tickers))
        return frame

    def save_factor_frame(
        self,
        market: str,
        tickers: list[str],
        frame: FactorFrame,
        snapshot_date: date | None = None,
    ) -> None:
        if not settings.snapshot_enabled or not tickers:
            return
        day = today_iso(snapshot_date)
        key = tickers_key(tickers)
        payload = factor_frame_to_json(frame)
        as_of = frame.as_of.date().isoformat()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO factor_snapshots (
                    snapshot_date, market, tickers_key, as_of, frame_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_date, market, tickers_key) DO UPDATE SET
                    as_of = excluded.as_of,
                    frame_json = excluded.frame_json,
                    created_at = excluded.created_at
                """,
                (day, market.upper(), key, as_of, payload, utc_now_iso()),
            )
            conn.commit()
        logger.info("Saved factor snapshot: %s %s (%d tickers)", day, market, len(tickers))

    def stats(self) -> dict[str, int]:
        with get_connection() as conn:
            universe_count = conn.execute(
                "SELECT COUNT(*) AS c FROM universe_snapshots"
            ).fetchone()["c"]
            factor_count = conn.execute(
                "SELECT COUNT(*) AS c FROM factor_snapshots"
            ).fetchone()["c"]
        return {
            "universe_snapshots": int(universe_count),
            "factor_snapshots": int(factor_count),
        }


_store: SnapshotStore | None = None


def get_snapshot_store() -> SnapshotStore:
    global _store
    if _store is None:
        _store = SnapshotStore()
    return _store
