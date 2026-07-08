import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.config import settings
from app.db.connection import init_database
from app.db.serializers import factor_frame_from_json, factor_frame_to_json, tickers_key
from app.db.snapshot_store import SnapshotStore
from app.factors.models import TickerFactorInputs
from app.factors.pipeline import FactorFrame


def _sample_frame() -> FactorFrame:
    tickers = ["005930", "000660"]
    inputs = TickerFactorInputs(
        pbr=0.9,
        universe_pbr=[0.9, 1.1],
        net_revision_ratio=0.05,
        earnings_surprise_pct=0.02,
        inst_net_daily=[1.0, 2.0],
        combined_net_daily=[-1.0, 0.5, 1.0],
        trading_values=[100.0, 200.0],
        closes=[100.0, 101.0],
        opens=[99.0, 100.0],
        volumes=[1000.0, 1100.0],
        current_roe=10.0,
        previous_roe=8.0,
    )
    return FactorFrame(
        tickers=tickers,
        prices=pd.Series({"005930": 70000.0, "000660": 200000.0}),
        pbr=pd.Series({"005930": 0.9, "000660": 1.2}),
        eps_revision_pct=pd.Series({"005930": 5.0}),
        revision_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        flow_turnaround_score=pd.Series({"005930": 0.5, "000660": 0.0}),
        vcp_score=pd.Series({"005930": 0.0, "000660": 0.0}),
        roe_turnaround_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        insider_score=pd.Series({"005930": 0.0, "000660": 0.0}),
        financial_stability_score=pd.Series({"005930": 1.0, "000660": 1.0}),
        factor_inputs={"005930": inputs, "000660": inputs},
        as_of=pd.Timestamp("2026-07-08"),
    )


def test_factor_frame_json_roundtrip():
    original = _sample_frame()
    restored = factor_frame_from_json(factor_frame_to_json(original))
    assert restored.tickers == original.tickers
    assert restored.revision_score["005930"] == 1.0
    assert restored.factor_inputs["005930"].pbr == 0.9


def test_snapshot_store_universe_and_factor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "sqlite_path", str(db_file))
    monkeypatch.setattr(settings, "snapshot_enabled", True)

    init_database()
    store = SnapshotStore()

    assert store.load_universe("KOSPI", date(2026, 7, 8)) is None

    store.save_universe("KOSPI", ["005930", "000660"], False, date(2026, 7, 8))
    loaded = store.load_universe("KOSPI", date(2026, 7, 8))
    assert loaded is not None
    assert loaded.tickers == ["005930", "000660"]
    assert loaded.used_fallback is False

    frame = _sample_frame()
    tickers = frame.tickers
    assert store.load_factor_frame("KOSPI", tickers, date(2026, 7, 8)) is None

    store.save_factor_frame("KOSPI", tickers, frame, date(2026, 7, 8))
    restored = store.load_factor_frame("KOSPI", tickers, date(2026, 7, 8))
    assert restored is not None
    assert restored.tickers == tickers
    assert float(restored.prices["005930"]) == 70000.0

    stats = store.stats()
    assert stats["universe_snapshots"] == 1
    assert stats["factor_snapshots"] == 1


def test_list_factor_snapshot_dates_and_best_frame(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "sqlite_path", str(db_file))
    monkeypatch.setattr(settings, "snapshot_enabled", True)

    init_database()
    store = SnapshotStore()

    frame_small = _sample_frame()
    frame_small.tickers = ["005930"]
    store.save_factor_frame("KOSPI", ["005930"], frame_small, date(2026, 7, 1))
    store.save_factor_frame("KOSPI", frame_small.tickers, _sample_frame(), date(2026, 7, 1))
    store.save_factor_frame("KOSPI", _sample_frame().tickers, _sample_frame(), date(2026, 7, 8))

    dates = store.list_factor_snapshot_dates("KOSPI")
    assert dates == [date(2026, 7, 1), date(2026, 7, 8)]

    best = store.load_best_factor_frame("KOSPI", date(2026, 7, 1))
    assert best is not None
    assert len(best.tickers) == 2


def test_tickers_key_is_order_independent():
    assert tickers_key(["000660", "005930"]) == tickers_key(["005930", "000660"])
