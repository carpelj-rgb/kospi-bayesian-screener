from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.config import settings
from app.data.providers.cache import cache_key, get_or_fetch
from app.data.providers.pykrx_client import PykrxClient
from app.data.providers.yfinance_client import YFinanceClient
from app.factors.models import TickerFactorInputs
from app.factors.revision_momentum import factor_revision_momentum
from app.factors.flow_turnaround import factor_flow_turnaround
from app.factors.vcp_breakout import factor_vcp_breakout
from app.factors.roe_turnaround import factor_roe_turnaround
from app.factors.insider_buying import factor_insider_buying
from app.factors.financial_stability import factor_financial_stability
from app.utils.sanitize import safe_optional_float

logger = logging.getLogger(__name__)


def _extract_ohlcv(df: pd.DataFrame) -> tuple[list[float], list[float], list[float], list[float]]:
    if df is None or df.empty:
        return [], [], [], []
    try:
        closes = df["종가"].astype(float).tolist() if "종가" in df.columns else []
        opens = df["시가"].astype(float).tolist() if "시가" in df.columns else closes
        volumes = df["거래량"].astype(float).tolist() if "거래량" in df.columns else []
        values = df["거래대금"].astype(float).tolist() if "거래대금" in df.columns else []
        return closes, opens, volumes, values
    except Exception:
        return [], [], [], []


@dataclass
class FactorFrame:
    tickers: list[str]
    prices: pd.Series
    pbr: pd.Series
    eps_revision_pct: pd.Series
    revision_score: pd.Series
    flow_turnaround_score: pd.Series
    vcp_score: pd.Series
    roe_turnaround_score: pd.Series
    insider_score: pd.Series
    financial_stability_score: pd.Series
    factor_inputs: dict[str, TickerFactorInputs]
    as_of: pd.Timestamp


def _neutral_inputs() -> TickerFactorInputs:
    return TickerFactorInputs(
        pbr=None,
        universe_pbr=[],
        net_revision_ratio=None,
        earnings_surprise_pct=None,
        inst_net_daily=[],
        combined_net_daily=[],
        trading_values=[],
        closes=[],
        opens=[],
        volumes=[],
        current_roe=None,
        previous_roe=None,
    )


def _empty_frame(tickers: list[str], as_of: date | None = None) -> FactorFrame:
    ts = pd.Timestamp(as_of or date.today())
    empty = pd.Series(dtype="float64")
    return FactorFrame(
        tickers=tickers,
        prices=empty,
        pbr=empty,
        eps_revision_pct=empty,
        revision_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        flow_turnaround_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        vcp_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        roe_turnaround_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        insider_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        financial_stability_score=pd.Series({t: 0.0 for t in tickers}, dtype="float64"),
        factor_inputs={t: _neutral_inputs() for t in tickers},
        as_of=ts,
    )


class FactorPipeline:
    def __init__(
        self,
        pykrx: PykrxClient | None = None,
        yfinance: YFinanceClient | None = None,
    ):
        self.pykrx = pykrx or PykrxClient()
        self.yfinance = yfinance or YFinanceClient()

    def _safe_fetch(self, label: str, fetcher, default):
        try:
            return fetcher()
        except Exception:
            logger.debug("%s fetch failed; using fallback", label, exc_info=True)
            return default

    def run(self, tickers: list[str], market: str = "KOSPI") -> FactorFrame:
        if not tickers:
            return _empty_frame([])

        key = cache_key(
            "pipeline",
            market.upper(),
            date.today().isoformat(),
            ",".join(sorted(tickers)),
        )
        return get_or_fetch(key, lambda: self._run_uncached(tickers, market))

    def _run_uncached(self, tickers: list[str], market: str = "KOSPI") -> FactorFrame:
        try:
            as_of = self.pykrx.latest_business_day()
        except Exception:
            logger.debug("latest_business_day failed; using today", exc_info=True)
            as_of = date.today()

        prices = self._safe_fetch("prices", lambda: self.pykrx.get_prices(tickers, as_of, market), pd.Series(dtype="float64"))
        pbr = self._safe_fetch("pbr", lambda: self.pykrx.get_pbr(tickers, as_of, market), pd.Series(dtype="float64"))
        revision_data = self._safe_fetch(
            "revision_data",
            lambda: self.yfinance.get_revision_data(tickers, market),
            {t: None for t in tickers},
        )
        insider_data = self._safe_fetch(
            "insider_data",
            lambda: self.yfinance.get_insider_data(tickers, market),
            {t: None for t in tickers},
        )
        financial_data = self._safe_fetch(
            "financial_data",
            lambda: self.yfinance.get_financial_stability_data(tickers, market),
            {t: None for t in tickers},
        )
        inst_net = self._safe_fetch(
            "inst_net",
            lambda: self.pykrx.get_inst_net_daily(tickers, as_of, settings.flow_short_window),
            {t: [] for t in tickers},
        )
        combined_net = self._safe_fetch(
            "combined_net",
            lambda: self.pykrx.get_combined_net_daily(
                tickers, as_of, settings.flow_long_window + settings.flow_short_window
            ),
            {t: [] for t in tickers},
        )
        ohlcv_map = self._safe_fetch(
            "ohlcv",
            lambda: self.pykrx.get_ohlcv_history(tickers, as_of, settings.vcp_lookback_days + 10),
            {t: pd.DataFrame() for t in tickers},
        )
        roe_map = self._safe_fetch(
            "roe",
            lambda: self.pykrx.get_roe_series(tickers, as_of),
            {t: (None, None) for t in tickers},
        )

        universe_pbr = [
            float(v)
            for v in pbr.dropna().tolist()
            if safe_optional_float(v) is not None and float(v) > 0
        ]
        debt_ratios = [
            ratio
            for t in tickers
            if (fin := financial_data.get(t)) is not None
            and (ratio := safe_optional_float(fin.debt_ratio)) is not None
        ]

        revision_flags: dict[str, float] = {}
        flow_flags: dict[str, float] = {}
        vcp_flags: dict[str, float] = {}
        roe_flags: dict[str, float] = {}
        insider_flags: dict[str, float] = {}
        financial_flags: dict[str, float] = {}
        factor_inputs: dict[str, TickerFactorInputs] = {}
        eps_revision_pct: dict[str, float] = {}

        for ticker in tickers:
            try:
                rev = revision_data.get(ticker) if revision_data else None
                net_rev = rev.net_revision_ratio if rev else None
                surprise = rev.earnings_surprise_pct if rev else None
                if net_rev is not None:
                    pct = safe_optional_float(net_rev * 100)
                    if pct is not None:
                        eps_revision_pct[ticker] = pct

                insider = insider_data.get(ticker) if insider_data else None
                financial = financial_data.get(ticker) if financial_data else None
                ohlcv = ohlcv_map.get(ticker, pd.DataFrame()) if ohlcv_map else pd.DataFrame()
                closes, opens, volumes, trading_values = _extract_ohlcv(ohlcv)
                current_roe, previous_roe = roe_map.get(ticker, (None, None)) if roe_map else (None, None)
                pbr_val = safe_optional_float(pbr.get(ticker)) if ticker in pbr else None

                inputs = TickerFactorInputs(
                    pbr=pbr_val,
                    universe_pbr=universe_pbr,
                    net_revision_ratio=safe_optional_float(net_rev),
                    earnings_surprise_pct=safe_optional_float(surprise),
                    inst_net_daily=inst_net.get(ticker, []) if inst_net else [],
                    combined_net_daily=combined_net.get(ticker, []) if combined_net else [],
                    trading_values=trading_values,
                    closes=closes,
                    opens=opens,
                    volumes=volumes,
                    current_roe=safe_optional_float(current_roe),
                    previous_roe=safe_optional_float(previous_roe),
                    insider_stake_increased=insider.stake_increased if insider else False,
                    insider_open_market_buy=insider.open_market_buy if insider else False,
                    debt_ratio=safe_optional_float(financial.debt_ratio) if financial else None,
                    universe_debt_ratios=debt_ratios,
                    operating_cash_flows_3y=financial.operating_cash_flows_3y if financial else [],
                )
                factor_inputs[ticker] = inputs

                revision_flags[ticker] = 1.0 if factor_revision_momentum(
                    inputs.net_revision_ratio, inputs.earnings_surprise_pct, inputs.inst_net_daily
                ) else 0.0
                flow_flags[ticker] = 1.0 if factor_flow_turnaround(
                    inputs.combined_net_daily, inputs.trading_values
                ) else 0.0
                vcp_flags[ticker] = 1.0 if factor_vcp_breakout(closes, opens, volumes) else 0.0
                roe_flags[ticker] = 1.0 if factor_roe_turnaround(
                    pbr_val, inputs.current_roe, inputs.previous_roe, universe_pbr
                ) else 0.0
                insider_flags[ticker] = 1.0 if factor_insider_buying(
                    inputs.insider_stake_increased, inputs.insider_open_market_buy
                ) else 0.0
                financial_flags[ticker] = 1.0 if factor_financial_stability(
                    inputs.debt_ratio, debt_ratios, inputs.operating_cash_flows_3y
                ) else 0.0
            except Exception:
                logger.exception("Factor evaluation failed for %s", ticker)
                factor_inputs[ticker] = _neutral_inputs()
                revision_flags[ticker] = 0.0
                flow_flags[ticker] = 0.0
                vcp_flags[ticker] = 0.0
                roe_flags[ticker] = 0.0
                insider_flags[ticker] = 0.0
                financial_flags[ticker] = 0.0

        return FactorFrame(
            tickers=tickers,
            prices=prices if prices is not None else pd.Series(dtype="float64"),
            pbr=pbr if pbr is not None else pd.Series(dtype="float64"),
            eps_revision_pct=pd.Series(eps_revision_pct, dtype="float64"),
            revision_score=pd.Series(revision_flags, dtype="float64"),
            flow_turnaround_score=pd.Series(flow_flags, dtype="float64"),
            vcp_score=pd.Series(vcp_flags, dtype="float64"),
            roe_turnaround_score=pd.Series(roe_flags, dtype="float64"),
            insider_score=pd.Series(insider_flags, dtype="float64"),
            financial_stability_score=pd.Series(financial_flags, dtype="float64"),
            factor_inputs=factor_inputs,
            as_of=pd.Timestamp(as_of),
        )
