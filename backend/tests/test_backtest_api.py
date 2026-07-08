from datetime import date
from unittest.mock import MagicMock

from app.api.v1.backtest import run_backtest_endpoint
from app.schemas.backtest import BacktestMetrics, BacktestResponse


def test_backtest_endpoint_passes_params():
    service = MagicMock()
    service.get_backtest.return_value = BacktestResponse(
        market="KOSPI",
        top_n=5,
        start_date=None,
        end_date=None,
        snapshot_dates_used=[date(2026, 7, 1)],
        metrics=BacktestMetrics(
            total_return=0.05,
            benchmark_total_return=0.02,
            max_drawdown=0.01,
            sharpe_ratio=1.2,
            periods=1,
            win_rate=1.0,
        ),
        equity_curve=[],
        periods=[],
        warnings=[],
    )

    run_backtest_endpoint(
        market="KOSPI",
        top_n=5,
        start_date=None,
        end_date=None,
        service=service,
    )

    service.get_backtest.assert_called_once_with(
        market="KOSPI",
        top_n=5,
        start_date=None,
        end_date=None,
    )
