from __future__ import annotations

import math


def compute_equity_curve(period_returns: list[float], *, start: float = 1.0) -> list[float]:
    """Convert period returns into a cumulative equity curve (includes start value)."""
    equity = [start]
    value = start
    for r in period_returns:
        value *= 1.0 + r
        equity.append(value)
    return equity


def compute_total_return(period_returns: list[float]) -> float:
    if not period_returns:
        return 0.0
    equity = compute_equity_curve(period_returns)
    return equity[-1] - 1.0


def compute_max_drawdown(equity_curve: list[float]) -> float:
    """Maximum drawdown as a positive fraction (e.g. 0.12 = 12% drawdown)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve[1:]:
        if value > peak:
            peak = value
        if peak > 0:
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
    return max_dd


def compute_sharpe_ratio(
    period_returns: list[float],
    *,
    periods_per_year: float = 252.0,
    risk_free_rate: float = 0.0,
) -> float | None:
    """Annualized Sharpe ratio; returns None when variance is zero."""
    if len(period_returns) < 2:
        return None
    rf_per_period = risk_free_rate / periods_per_year
    excess = [r - rf_per_period for r in period_returns]
    mean = sum(excess) / len(excess)
    variance = sum((x - mean) ** 2 for x in excess) / (len(excess) - 1)
    if variance <= 0:
        return None
    std = math.sqrt(variance)
    if std == 0:
        return None
    return (mean / std) * math.sqrt(periods_per_year)


def compute_win_rate(period_returns: list[float]) -> float:
    if not period_returns:
        return 0.0
    wins = sum(1 for r in period_returns if r > 0)
    return wins / len(period_returns)
