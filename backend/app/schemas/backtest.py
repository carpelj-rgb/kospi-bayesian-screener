from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class BacktestMetrics(BaseModel):
    total_return: float = Field(description="Cumulative portfolio return")
    benchmark_total_return: float = Field(description="Cumulative equal-weight universe return")
    max_drawdown: float = Field(description="Maximum drawdown (positive fraction)")
    sharpe_ratio: float | None = Field(description="Annualized Sharpe ratio")
    periods: int = Field(description="Number of rebalance periods")
    win_rate: float = Field(description="Fraction of periods with positive return")


class BacktestEquityPoint(BaseModel):
    date: date
    portfolio: float
    benchmark: float


class BacktestPeriodRow(BaseModel):
    rebalance_date: date
    next_date: date
    holdings: list[str]
    period_return: float
    benchmark_return: float


class BacktestResponse(BaseModel):
    market: str
    top_n: int
    start_date: date | None
    end_date: date | None
    snapshot_dates_used: list[date]
    metrics: BacktestMetrics
    equity_curve: list[BacktestEquityPoint]
    periods: list[BacktestPeriodRow]
    warnings: list[str] = Field(default_factory=list)
