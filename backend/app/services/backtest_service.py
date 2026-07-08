from __future__ import annotations

from datetime import date

from app.backtest.engine import BacktestEngineResult, run_backtest
from app.schemas.backtest import (
    BacktestEquityPoint,
    BacktestMetrics,
    BacktestPeriodRow,
    BacktestResponse,
)


class BacktestService:
    def get_backtest(
        self,
        *,
        market: str = "KOSPI",
        top_n: int = 10,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> BacktestResponse:
        result = run_backtest(
            market=market,
            top_n=top_n,
            start_date=start_date,
            end_date=end_date,
        )
        return self._to_response(result, start_date=start_date, end_date=end_date)

    def _to_response(
        self,
        result: BacktestEngineResult,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> BacktestResponse:
        equity_curve = self._build_equity_curve(result)
        return BacktestResponse(
            market=result.market,
            top_n=result.top_n,
            start_date=start_date,
            end_date=end_date,
            snapshot_dates_used=result.snapshot_dates_used,
            metrics=BacktestMetrics(
                total_return=result.total_return,
                benchmark_total_return=result.benchmark_total_return,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                periods=len(result.periods),
                win_rate=result.win_rate,
            ),
            equity_curve=equity_curve,
            periods=[
                BacktestPeriodRow(
                    rebalance_date=p.rebalance_date,
                    next_date=p.next_date,
                    holdings=p.holdings,
                    period_return=p.period_return,
                    benchmark_return=p.benchmark_return,
                )
                for p in result.periods
            ],
            warnings=result.warnings,
        )

    def _build_equity_curve(self, result: BacktestEngineResult) -> list[BacktestEquityPoint]:
        if not result.periods:
            return []

        portfolio_eq = result.portfolio_equity
        benchmark_eq = result.benchmark_equity
        points: list[BacktestEquityPoint] = [
            BacktestEquityPoint(
                date=result.periods[0].rebalance_date,
                portfolio=portfolio_eq[0],
                benchmark=benchmark_eq[0],
            )
        ]
        for idx, period in enumerate(result.periods):
            points.append(
                BacktestEquityPoint(
                    date=period.next_date,
                    portfolio=portfolio_eq[idx + 1],
                    benchmark=benchmark_eq[idx + 1],
                )
            )
        return points
