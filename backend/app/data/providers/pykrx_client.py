from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd

from app.data.providers.krx_config import get_stock_module, should_use_pykrx
from app.data.universe import get_ticker_name


def _to_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _latest_business_day(reference: date | None = None) -> date:
    ref = reference or date.today()
    if not should_use_pykrx():
        return ref
    stock = get_stock_module()
    for offset in range(0, 14):
        candidate = ref - timedelta(days=offset)
        ymd = _to_yyyymmdd(candidate)
        try:
            df = stock.get_market_ohlcv_by_date(ymd, ymd, "005930")
            if df is not None and not df.empty:
                return candidate
        except Exception:
            continue
    return ref


class PykrxClient:
    def __init__(self) -> None:
        self._enabled = should_use_pykrx()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def latest_business_day(self, reference: date | None = None) -> date:
        return _latest_business_day(reference)

    def get_prices(self, tickers: list[str], as_of: date, market: str = "KOSPI") -> pd.Series:
        if not self._enabled:
            return pd.Series(dtype="float64")
        stock = get_stock_module()
        ymd = _to_yyyymmdd(as_of)
        try:
            df = stock.get_market_ohlcv_by_ticker(ymd, market=market)
            if df is not None and not df.empty:
                close_col = "종가" if "종가" in df.columns else df.columns[0]
                series = df[close_col].astype("float64")
                return series.reindex(tickers).dropna(how="all")
        except Exception:
            pass

        prices: dict[str, float] = {}
        for ticker in tickers:
            try:
                df = stock.get_market_ohlcv_by_date(ymd, ymd, ticker)
                if df is not None and not df.empty:
                    prices[ticker] = float(df["종가"].iloc[-1])
            except Exception:
                continue
        return pd.Series(prices, dtype="float64")

    def get_pbr(self, tickers: list[str], as_of: date, market: str = "KOSPI") -> pd.Series:
        if not self._enabled:
            return pd.Series(dtype="float64")
        stock = get_stock_module()
        ymd = _to_yyyymmdd(as_of)
        try:
            df = stock.get_market_fundamental_by_ticker(ymd, market=market)
            if df is not None and not df.empty and "PBR" in df.columns:
                pbr = df["PBR"].astype("float64")
                pbr = pbr[pbr > 0]
                return pbr.reindex(tickers).dropna(how="all")
        except Exception:
            pass

        values: dict[str, float] = {}
        for ticker in tickers:
            try:
                df = stock.get_market_fundamental_by_date(ymd, ymd, ticker)
                if df is not None and not df.empty and "PBR" in df.columns:
                    pbr = float(df["PBR"].iloc[-1])
                    if pd.notna(pbr) and pbr > 0:
                        values[ticker] = pbr
            except Exception:
                continue
        return pd.Series(values, dtype="float64")

    def _net_flow_for_ticker(
        self, ticker: str, ymd_start: str, ymd_end: str, window: int
    ) -> dict[str, float | str] | None:
        stock = get_stock_module()
        try:
            foreign = stock.get_market_net_purchases_of_equities(
                ymd_start, ymd_end, ticker, "외국인"
            )
            inst = stock.get_market_net_purchases_of_equities(
                ymd_start, ymd_end, ticker, "기관"
            )
            if foreign is None or foreign.empty:
                return None
            combined = foreign["순매수거래대금"].fillna(0)
            if inst is not None and not inst.empty:
                combined = combined.add(inst["순매수거래대금"].fillna(0), fill_value=0)
            tail = combined.tail(window)
            return {
                "ticker": ticker,
                "net_flow_sum": float(tail.sum()),
                "net_flow_mean": float(tail.mean()) if len(tail) else 0.0,
            }
        except Exception:
            return None

    def get_inst_net_daily(
        self, tickers: list[str], as_of: date, days: int = 5
    ) -> dict[str, list[float]]:
        if not self._enabled:
            return {ticker: [] for ticker in tickers}
        stock = get_stock_module()
        start = as_of - timedelta(days=days * 3)
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)
        result: dict[str, list[float]] = {ticker: [] for ticker in tickers}
        workers = min(8, max(1, len(tickers)))

        def _fetch(ticker: str) -> tuple[str, list[float]]:
            try:
                inst = stock.get_market_net_purchases_of_equities(
                    ymd_start, ymd_end, ticker, "기관"
                )
                if inst is None or inst.empty:
                    return ticker, []
                values = inst["순매수거래대금"].fillna(0).astype(float).tolist()
                return ticker, values[-days:]
            except Exception:
                return ticker, []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetch, ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker, values = future.result()
                result[ticker] = values
        return result

    def get_combined_net_daily(
        self, tickers: list[str], as_of: date, days: int = 25
    ) -> dict[str, list[float]]:
        if not self._enabled:
            return {ticker: [] for ticker in tickers}
        stock = get_stock_module()
        start = as_of - timedelta(days=days * 3)
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)
        result: dict[str, list[float]] = {ticker: [] for ticker in tickers}
        workers = min(8, max(1, len(tickers)))

        def _fetch(ticker: str) -> tuple[str, list[float]]:
            try:
                foreign = stock.get_market_net_purchases_of_equities(
                    ymd_start, ymd_end, ticker, "외국인"
                )
                inst = stock.get_market_net_purchases_of_equities(
                    ymd_start, ymd_end, ticker, "기관"
                )
                if foreign is None or foreign.empty:
                    return ticker, []
                combined = foreign["순매수거래대금"].fillna(0).astype(float)
                if inst is not None and not inst.empty:
                    combined = combined.add(
                        inst["순매수거래대금"].fillna(0), fill_value=0
                    )
                return ticker, combined.tolist()[-days:]
            except Exception:
                return ticker, []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetch, ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker, values = future.result()
                result[ticker] = values
        return result

    def get_ohlcv_history(
        self, tickers: list[str], as_of: date, days: int = 130
    ) -> dict[str, pd.DataFrame]:
        if not self._enabled:
            return {ticker: pd.DataFrame() for ticker in tickers}
        stock = get_stock_module()
        start = as_of - timedelta(days=int(days * 1.6))
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)
        result: dict[str, pd.DataFrame] = {}
        workers = min(8, max(1, len(tickers)))

        def _fetch(ticker: str) -> tuple[str, pd.DataFrame]:
            try:
                df = stock.get_market_ohlcv_by_date(ymd_start, ymd_end, ticker)
                if df is None or df.empty:
                    return ticker, pd.DataFrame()
                return ticker, df.tail(days)
            except Exception:
                return ticker, pd.DataFrame()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetch, ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker, df = future.result()
                result[ticker] = df
        return result

    def get_roe_series(
        self, tickers: list[str], as_of: date, periods: int = 2
    ) -> dict[str, tuple[float | None, float | None]]:
        if not self._enabled:
            return {ticker: (None, None) for ticker in tickers}
        stock = get_stock_module()
        start = as_of - timedelta(days=periods * 120)
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)
        result: dict[str, tuple[float | None, float | None]] = {
            ticker: (None, None) for ticker in tickers
        }
        workers = min(8, max(1, len(tickers)))

        def _roe_from_row(row) -> float | None:
            eps = float(row.get("EPS", float("nan")))
            bps = float(row.get("BPS", float("nan")))
            if pd.notna(eps) and pd.notna(bps) and bps > 0:
                return eps / bps * 100
            return None

        def _fetch(ticker: str) -> tuple[str, tuple[float | None, float | None]]:
            try:
                df = stock.get_market_fundamental_by_date(ymd_start, ymd_end, ticker)
                if df is None or df.empty:
                    return ticker, (None, None)
                roes = [_roe_from_row(df.iloc[i]) for i in range(len(df))]
                roes = [r for r in roes if r is not None]
                if len(roes) >= 2:
                    return ticker, (roes[-1], roes[-2])
                if len(roes) == 1:
                    return ticker, (roes[-1], None)
                return ticker, (None, None)
            except Exception:
                return ticker, (None, None)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetch, ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker, roe_pair = future.result()
                result[ticker] = roe_pair
        return result

    def get_foreign_net_daily(
        self, tickers: list[str], as_of: date, days: int = 5
    ) -> dict[str, list[float]]:
        if not self._enabled:
            return {ticker: [] for ticker in tickers}
        stock = get_stock_module()
        start = as_of - timedelta(days=days * 3)
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)

        result: dict[str, list[float]] = {ticker: [] for ticker in tickers}
        workers = min(8, max(1, len(tickers)))

        def _fetch(ticker: str) -> tuple[str, list[float]]:
            try:
                foreign = stock.get_market_net_purchases_of_equities(
                    ymd_start, ymd_end, ticker, "외국인"
                )
                if foreign is None or foreign.empty:
                    return ticker, []
                values = foreign["순매수거래대금"].fillna(0).astype(float).tolist()
                return ticker, values[-days:]
            except Exception:
                return ticker, []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetch, ticker) for ticker in tickers]
            for future in as_completed(futures):
                ticker, values = future.result()
                result[ticker] = values
        return result

    def get_net_flow(self, tickers: list[str], as_of: date, window: int) -> pd.DataFrame:
        if not self._enabled:
            return pd.DataFrame(columns=["ticker", "net_flow_sum", "net_flow_mean"])
        start = as_of - timedelta(days=window * 2)
        ymd_start = _to_yyyymmdd(start)
        ymd_end = _to_yyyymmdd(as_of)

        rows: list[dict[str, float | str]] = []
        workers = min(8, max(1, len(tickers)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._net_flow_for_ticker, ticker, ymd_start, ymd_end, window): ticker
                for ticker in tickers
            }
            for future in as_completed(futures):
                row = future.result()
                if row:
                    rows.append(row)

        if not rows:
            return pd.DataFrame(columns=["ticker", "net_flow_sum", "net_flow_mean"])
        return pd.DataFrame(rows).set_index("ticker")

    def get_names(self, tickers: list[str]) -> dict[str, str]:
        return {ticker: get_ticker_name(ticker) for ticker in tickers}
