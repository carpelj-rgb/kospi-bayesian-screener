from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date

import pandas as pd
import yfinance as yf

from app.data.providers.cache import cache_key, get_or_fetch
from app.data.providers.financial_models import FinancialStabilityData, InsiderData


@dataclass
class RevisionData:
    net_revision_ratio: float | None
    earnings_surprise_pct: float | None


class YFinanceClient:
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

    def _symbol(self, ticker: str, market: str) -> str:
        suffix = ".KS" if market.upper() == "KOSPI" else ".KQ"
        return f"{ticker}{suffix}"

    def _fetch_parallel(
        self,
        tickers: list[str],
        market: str,
        worker,
    ) -> dict[str, object]:
        results: dict[str, object] = {}
        workers = min(self.max_workers, max(1, len(tickers)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(worker, ticker, self._symbol(ticker, market)): ticker
                for ticker in tickers
            }
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    results[ticker] = future.result()
                except Exception:
                    results[ticker] = None
        return results

    def get_revision_data(
        self, tickers: list[str], market: str = "KOSPI"
    ) -> dict[str, RevisionData]:
        key = cache_key(
            "yf:revision",
            market.upper(),
            date.today().isoformat(),
            ",".join(sorted(tickers)),
        )
        return get_or_fetch(key, lambda: self._fetch_revision_data(tickers, market))

    def _fetch_revision_data(
        self, tickers: list[str], market: str
    ) -> dict[str, RevisionData]:
        def _one(ticker: str, symbol: str) -> RevisionData:
            t = yf.Ticker(symbol)
            return RevisionData(
                self._net_revision_ratio(t),
                self._earnings_surprise_pct(t),
            )

        raw = self._fetch_parallel(tickers, market, _one)
        return {
            t: raw.get(t) or RevisionData(None, None)
            for t in tickers
        }

    def get_insider_data(
        self, tickers: list[str], market: str = "KOSPI"
    ) -> dict[str, InsiderData]:
        key = cache_key(
            "yf:insider",
            market.upper(),
            date.today().isoformat(),
            ",".join(sorted(tickers)),
        )
        return get_or_fetch(key, lambda: self._fetch_insider_data(tickers, market))

    def _fetch_insider_data(
        self, tickers: list[str], market: str
    ) -> dict[str, InsiderData]:
        def _one(ticker: str, symbol: str) -> InsiderData:
            return self._parse_insider_data(yf.Ticker(symbol))

        raw = self._fetch_parallel(tickers, market, _one)
        return {
            t: raw.get(t) or InsiderData(stake_increased=False, open_market_buy=False)
            for t in tickers
        }

    def get_financial_stability_data(
        self, tickers: list[str], market: str = "KOSPI"
    ) -> dict[str, FinancialStabilityData]:
        key = cache_key(
            "yf:financial",
            market.upper(),
            date.today().isoformat(),
            ",".join(sorted(tickers)),
        )
        return get_or_fetch(key, lambda: self._fetch_financial_stability_data(tickers, market))

    def _fetch_financial_stability_data(
        self, tickers: list[str], market: str
    ) -> dict[str, FinancialStabilityData]:
        def _one(ticker: str, symbol: str) -> FinancialStabilityData:
            return self._parse_financial_stability(yf.Ticker(symbol))

        raw = self._fetch_parallel(tickers, market, _one)
        return {
            t: raw.get(t) or FinancialStabilityData(debt_ratio=None, operating_cash_flows_3y=[])
            for t in tickers
        }

    def _net_revision_ratio(self, ticker: yf.Ticker) -> float | None:
        try:
            estimates = ticker.earnings_estimate
            if estimates is None or estimates.empty:
                return None
            growths: list[float] = []
            for key in ("0q", "+1q", "0y"):
                if key in estimates.index:
                    g = estimates.loc[key].get("growth")
                    if g is not None and pd.notna(g):
                        growths.append(float(g))
            if growths:
                return sum(growths) / len(growths)
            row = estimates.iloc[0]
            growth = float(row.get("growth", float("nan")))
            if pd.notna(growth):
                return growth
            return None
        except Exception:
            return None

    def _earnings_surprise_pct(self, ticker: yf.Ticker) -> float | None:
        try:
            history = ticker.earnings_history
            if history is None or history.empty:
                return None
            row = history.iloc[0]
            actual = float(row.get("epsActual", float("nan")))
            estimate = float(row.get("epsEstimate", float("nan")))
            if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                return (actual - estimate) / abs(estimate)
            diff = row.get("surprisePercent")
            if diff is not None and pd.notna(diff):
                return float(diff) / 100
            return None
        except Exception:
            return None

    def _parse_insider_data(self, ticker: yf.Ticker) -> InsiderData:
        open_market_buy = False
        stake_increased = False

        try:
            tx = ticker.insider_transactions
            if tx is not None and not tx.empty:
                for _, row in tx.head(20).iterrows():
                    text = " ".join(str(v).lower() for v in row.values if v is not None)
                    if any(k in text for k in ("purchase", "buy", "매수", "취득")):
                        open_market_buy = True
                        break
        except Exception:
            pass

        try:
            holders = ticker.major_holders
            if holders is not None and not holders.empty:
                for val in holders.iloc[:, 0].astype(str):
                    if "%" in val and float(val.replace("%", "").strip()) > 0:
                        stake_increased = True
                        break
        except Exception:
            pass

        return InsiderData(stake_increased=stake_increased, open_market_buy=open_market_buy)

    def _parse_financial_stability(self, ticker: yf.Ticker) -> FinancialStabilityData:
        debt_ratio: float | None = None
        ocf_values: list[float] = []

        try:
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                debt = self._first_row_value(bs, ("Total Debt", "Total Liabilities Net Minority Interest"))
                equity = self._first_row_value(
                    bs, ("Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity")
                )
                if debt is not None and equity is not None and equity > 0:
                    debt_ratio = float(debt) / float(equity)
        except Exception:
            pass

        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                row = self._find_row(cf, ("Operating Cash Flow", "Total Cash From Operating Activities"))
                if row is not None:
                    for val in row.iloc[:3]:
                        if pd.notna(val):
                            ocf_values.append(float(val))
        except Exception:
            pass

        return FinancialStabilityData(debt_ratio=debt_ratio, operating_cash_flows_3y=ocf_values)

    @staticmethod
    def _first_row_value(df: pd.DataFrame, names: tuple[str, ...]) -> float | None:
        for name in names:
            if name in df.index:
                val = df.loc[name].iloc[0]
                if pd.notna(val):
                    return float(val)
        return None

    @staticmethod
    def _find_row(df: pd.DataFrame, names: tuple[str, ...]) -> pd.Series | None:
        for name in names:
            if name in df.index:
                return df.loc[name]
        return None

    def get_eps_revision(self, tickers: list[str], market: str = "KOSPI") -> pd.Series:
        data = self.get_revision_data(tickers, market)
        return pd.Series(
            {
                t: d.net_revision_ratio * 100 if d.net_revision_ratio is not None else float("nan")
                for t, d in data.items()
            },
            dtype="float64",
        )
