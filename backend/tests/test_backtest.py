from datetime import date

import pandas as pd
import pytest

from app.backtest.engine import run_backtest
from app.backtest.metrics import (
    compute_equity_curve,
    compute_max_drawdown,
    compute_sharpe_ratio,
    compute_total_return,
    compute_win_rate,
)
from app.config import settings
from app.db.connection import init_database
from app.db.snapshot_store import SnapshotStore
from app.factors.models import TickerFactorInputs
from app.factors.pipeline import FactorFrame


def test_compute_equity_curve_and_total_return():
    returns = [0.10, -0.05, 0.02]
    equity = compute_equity_curve(returns)
    assert equity == pytest.approx([1.0, 1.1, 1.045, 1.0659], rel=1e-4)
    assert compute_total_return(returns) == pytest.approx(0.0659, rel=1e-4)


def test_compute_max_drawdown():
    equity = [1.0, 1.2, 0.9, 1.0]
    assert compute_max_drawdown(equity) == pytest.approx(0.25)


def test_compute_sharpe_ratio():
    returns = [0.01, 0.02, -0.005, 0.015, 0.008]
    sharpe = compute_sharpe_ratio(returns, periods_per_year=252)
    assert sharpe is not None
    assert sharpe > 0


def test_compute_win_rate():
    assert compute_win_rate([0.1, -0.05, 0.0, 0.02]) == 0.5


def _frame_with_prices(
    tickers: list[str],
    prices: dict[str, float],
    as_of: date,
    revision_scores: dict[str, float] | None = None,
) -> FactorFrame:
    revision_scores = revision_scores or {t: 1.0 for t in tickers}
    inputs = TickerFactorInputs(
        pbr=0.8,
        universe_pbr=[0.8, 1.2],
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
        prices=pd.Series(prices, dtype="float64"),
        pbr=pd.Series({t: 1.0 for t in tickers}, dtype="float64"),
        eps_revision_pct=pd.Series({t: 5.0 for t in tickers}, dtype="float64"),
        revision_score=pd.Series(revision_scores, dtype="float64"),
        flow_turnaround_score=pd.Series({t: 1.0 for t in tickers}, dtype="float64"),
        vcp_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        roe_turnaround_score=pd.Series({t: 1.0 for t in tickers}, dtype="float64"),
        insider_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        financial_stability_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        factor_inputs={t: inputs for t in tickers},
        as_of=pd.Timestamp(as_of),
    )


def test_run_backtest_with_mock_prices(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "sqlite_path", str(db_file))
    monkeypatch.setattr(settings, "snapshot_enabled", True)
    init_database()
    store = SnapshotStore()

    day1 = date(2026, 7, 1)
    day2 = date(2026, 7, 8)
    tickers = ["005930", "000660", "035420"]

    store.save_factor_frame("KOSPI", tickers, _frame_with_prices(tickers, {
        "005930": 70000.0,
        "000660": 200000.0,
        "035420": 300000.0,
    }, day1), day1)
    store.save_factor_frame("KOSPI", tickers, _frame_with_prices(tickers, {
        "005930": 77000.0,
        "000660": 210000.0,
        "035420": 285000.0,
    }, day2, revision_scores={"005930": 1.0, "000660": 0.0, "035420": 0.0}), day2)

    price_table = {
        day1: {"005930": 70000.0, "000660": 200000.0, "035420": 300000.0},
        day2: {"005930": 77000.0, "000660": 210000.0, "035420": 285000.0},
    }

    def mock_prices(t: list[str], as_of: date, market: str) -> dict[str, float]:
        return {k: price_table[as_of][k] for k in t if k in price_table.get(as_of, {})}

    result = run_backtest(market="KOSPI", top_n=1, store=store, fetch_prices=mock_prices)

    assert len(result.periods) == 1
    assert result.periods[0].holdings == ["005930"]
    assert result.periods[0].period_return == pytest.approx(0.10)
    assert result.total_return == pytest.approx(0.10)
    assert result.max_drawdown == pytest.approx(0.0)


def test_run_backtest_insufficient_snapshots(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "sqlite_path", str(db_file))
    monkeypatch.setattr(settings, "snapshot_enabled", True)
    init_database()
    store = SnapshotStore()

    day1 = date(2026, 7, 1)
    tickers = ["005930"]
    store.save_factor_frame("KOSPI", tickers, _frame_with_prices(tickers, {"005930": 70000.0}, day1), day1)

    result = run_backtest(market="KOSPI", top_n=1, store=store, fetch_prices=lambda *_: {})
    assert result.periods == []
    assert any("2일 미만" in w for w in result.warnings)
