from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.backtest.metrics import (
    compute_equity_curve,
    compute_max_drawdown,
    compute_sharpe_ratio,
    compute_total_return,
    compute_win_rate,
)
from app.bayesian.screener import evaluate_screener_posterior, set_prior_odds
from app.config import settings
from app.db.snapshot_store import SnapshotStore, get_snapshot_store
from app.factors.pipeline import FactorFrame

logger = logging.getLogger(__name__)


class PriceFetcher(Protocol):
    def __call__(self, tickers: list[str], as_of: date, market: str) -> dict[str, float]: ...


@dataclass
class RebalancePeriod:
    rebalance_date: date
    next_date: date
    holdings: list[str]
    period_return: float
    benchmark_return: float


@dataclass
class BacktestEngineResult:
    market: str
    top_n: int
    snapshot_dates_used: list[date]
    portfolio_returns: list[float]
    benchmark_returns: list[float]
    periods: list[RebalancePeriod]
    warnings: list[str] = field(default_factory=list)

    @property
    def portfolio_equity(self) -> list[float]:
        return compute_equity_curve(self.portfolio_returns)

    @property
    def benchmark_equity(self) -> list[float]:
        return compute_equity_curve(self.benchmark_returns)

    @property
    def total_return(self) -> float:
        return compute_total_return(self.portfolio_returns)

    @property
    def benchmark_total_return(self) -> float:
        return compute_total_return(self.benchmark_returns)

    @property
    def max_drawdown(self) -> float:
        return compute_max_drawdown(self.portfolio_equity)

    @property
    def sharpe_ratio(self) -> float | None:
        return compute_sharpe_ratio(self.portfolio_returns)

    @property
    def win_rate(self) -> float:
        return compute_win_rate(self.portfolio_returns)


def _score_tickers(frame: FactorFrame) -> list[tuple[str, float]]:
    prior_odds = set_prior_odds(settings.prior_up_prob)
    scored: list[tuple[str, float]] = []
    for ticker in frame.tickers:
        inputs = frame.factor_inputs.get(ticker)
        if inputs is None:
            continue
        try:
            result = evaluate_screener_posterior(inputs, prior_odds=prior_odds)
            scored.append((ticker, result.posterior_up_prob))
        except Exception:
            logger.debug("Bayes scoring failed for %s", ticker, exc_info=True)
            continue
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def _resolve_prices(
    tickers: list[str],
    as_of: date,
    market: str,
    fetch_prices: PriceFetcher,
    frame: FactorFrame | None = None,
) -> dict[str, float]:
    prices = fetch_prices(tickers, as_of, market)
    if frame is not None and frame.as_of.date() == as_of:
        for ticker in tickers:
            if ticker in prices:
                continue
            try:
                value = float(frame.prices[ticker])
            except (KeyError, TypeError, ValueError):
                continue
            if value > 0:
                prices[ticker] = value
    return prices


def _equal_weight_return(
    tickers: list[str],
    start_prices: dict[str, float],
    end_prices: dict[str, float],
) -> float | None:
    returns: list[float] = []
    for ticker in tickers:
        start = start_prices.get(ticker)
        end = end_prices.get(ticker)
        if start is None or end is None or start <= 0:
            continue
        returns.append((end / start) - 1.0)
    if not returns:
        return None
    return sum(returns) / len(returns)


def run_backtest(
    *,
    market: str = "KOSPI",
    top_n: int = 10,
    start_date: date | None = None,
    end_date: date | None = None,
    store: SnapshotStore | None = None,
    fetch_prices: PriceFetcher | None = None,
) -> BacktestEngineResult:
    """
    Walk forward over SQLite factor snapshots:
    score tickers at each snapshot date, hold equal-weight top_n until the next date.
    """
    snapshot_store = store or get_snapshot_store()
    warnings: list[str] = []

    snapshot_dates = snapshot_store.list_factor_snapshot_dates(
        market, start_date=start_date, end_date=end_date
    )
    if len(snapshot_dates) < 2:
        warnings.append(
            "백테스트에 필요한 팩터 스냅샷이 2일 미만입니다. "
            "스크리너를 여러 날짜에 실행해 스냅샷을 쌓은 뒤 다시 시도하세요."
        )
        return BacktestEngineResult(
            market=market.upper(),
            top_n=top_n,
            snapshot_dates_used=snapshot_dates,
            portfolio_returns=[],
            benchmark_returns=[],
            periods=[],
            warnings=warnings,
        )

    price_fetcher = fetch_prices
    if price_fetcher is None:
        from app.data.providers.pykrx_client import PykrxClient

        pykrx = PykrxClient()

        def _default_fetch(tickers: list[str], as_of: date, mkt: str) -> dict[str, float]:
            if not pykrx.enabled:
                return {}
            series = pykrx.get_prices(tickers, as_of, market=mkt)
            return {str(k): float(v) for k, v in series.items() if v and float(v) > 0}

        price_fetcher = _default_fetch
        if not pykrx.enabled:
            warnings.append(
                "pykrx가 비활성화되어 스냅샷에 저장된 가격만 사용합니다. "
                "수익률 계산이 제한될 수 있습니다."
            )

    periods: list[RebalancePeriod] = []
    portfolio_returns: list[float] = []
    benchmark_returns: list[float] = []
    dates_used: list[date] = []

    for idx in range(len(snapshot_dates) - 1):
        rebalance_date = snapshot_dates[idx]
        next_date = snapshot_dates[idx + 1]
        frame = snapshot_store.load_best_factor_frame(market, rebalance_date)
        if frame is None:
            warnings.append(f"{rebalance_date.isoformat()} 팩터 스냅샷을 불러오지 못했습니다.")
            continue

        scored = _score_tickers(frame)
        if not scored:
            warnings.append(f"{rebalance_date.isoformat()} 점수 산출 가능한 종목이 없습니다.")
            continue

        holdings = [ticker for ticker, _ in scored[:top_n]]
        benchmark_universe = [ticker for ticker, _ in scored]

        start_prices = _resolve_prices(
            list(set(holdings + benchmark_universe)),
            rebalance_date,
            market,
            price_fetcher,
            frame=frame,
        )
        end_prices = _resolve_prices(
            list(set(holdings + benchmark_universe)),
            next_date,
            market,
            price_fetcher,
        )

        period_return = _equal_weight_return(holdings, start_prices, end_prices)
        bench_return = _equal_weight_return(benchmark_universe, start_prices, end_prices)

        if period_return is None:
            warnings.append(
                f"{rebalance_date.isoformat()}→{next_date.isoformat()} "
                "구간 수익률을 계산하지 못했습니다 (가격 데이터 부족)."
            )
            continue

        dates_used.append(rebalance_date)
        portfolio_returns.append(period_return)
        benchmark_returns.append(bench_return if bench_return is not None else 0.0)
        periods.append(
            RebalancePeriod(
                rebalance_date=rebalance_date,
                next_date=next_date,
                holdings=holdings,
                period_return=period_return,
                benchmark_return=bench_return if bench_return is not None else 0.0,
            )
        )

    if not periods:
        warnings.append("유효한 리밸런싱 구간이 없습니다.")

    return BacktestEngineResult(
        market=market.upper(),
        top_n=top_n,
        snapshot_dates_used=dates_used or snapshot_dates,
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        periods=periods,
        warnings=warnings,
    )
