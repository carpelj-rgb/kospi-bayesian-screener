from __future__ import annotations

import logging
import math
from datetime import date

from app.bayesian.screener import (
    CORE_FACTOR_WEIGHTS,
    FACTOR_TAG_LABELS,
    evaluate_screener_posterior,
    set_prior_odds,
)
from app.config import settings
from app.data.providers.pykrx_client import PykrxClient
from app.data.universe import get_tickers
from app.factors.models import TickerFactorInputs
from app.factors.pipeline import FactorFrame, FactorPipeline
from app.schemas.screener import FactorBreakdown, ScreenerRow, ScreenerResponse, StockDetailResponse
from app.utils.sanitize import safe_optional_float, safe_probability, safe_unit_score

logger = logging.getLogger(__name__)

FACTOR_SCORE_KEYS = {
    "revision_momentum": "revision_score",
    "flow_turnaround": "flow_turnaround_score",
    "vcp_breakout": "vcp_score",
    "roe_turnaround": "roe_turnaround_score",
    "insider_buying": "insider_score",
    "financial_stability": "financial_stability_score",
}


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


def _neutral_bayes():
    return evaluate_screener_posterior(_neutral_inputs(), prior_odds=set_prior_odds(settings.prior_up_prob))


class ScreenerService:
    def __init__(
        self,
        pipeline: FactorPipeline | None = None,
        pykrx: PykrxClient | None = None,
    ):
        self.pipeline = pipeline or FactorPipeline()
        self.pykrx = pykrx or PykrxClient()
        self._prior_odds = set_prior_odds(settings.prior_up_prob)

    def _resolve_tickers(self, market: str, limit: int | None) -> list[str]:
        tickers = get_tickers(market)
        cap = limit or settings.universe_limit
        return tickers[:cap]

    def _evaluate(self, frame: FactorFrame, ticker: str):
        inputs = frame.factor_inputs.get(ticker)
        if inputs is None:
            return _neutral_bayes()
        try:
            return evaluate_screener_posterior(inputs, prior_odds=self._prior_odds)
        except Exception:
            logger.exception("Bayesian evaluation failed for %s", ticker)
            return _neutral_bayes()

    def _series_value(self, series, ticker: str, default: float = 0.0) -> float:
        try:
            if ticker not in series.index and ticker not in series:
                return default
            value = series.get(ticker, default)
            return safe_unit_score(value, default)
        except Exception:
            return default

    def _row_from_frame(
        self,
        frame: FactorFrame,
        ticker: str,
        name: str,
        market: str,
        bayes,
        rank: int,
    ) -> ScreenerRow:
        eps_raw = None
        try:
            if ticker in frame.eps_revision_pct.index or ticker in frame.eps_revision_pct:
                eps_raw = safe_optional_float(frame.eps_revision_pct.get(ticker))
        except Exception:
            eps_raw = None

        return ScreenerRow(
            ticker=ticker,
            name=name,
            market=market,
            price=safe_optional_float(frame.prices.get(ticker)) if ticker in frame.prices else None,
            pbr=safe_optional_float(frame.pbr.get(ticker)) if ticker in frame.pbr else None,
            eps_revision_pct=eps_raw,
            revision_score=self._series_value(frame.revision_score, ticker),
            flow_turnaround_score=self._series_value(frame.flow_turnaround_score, ticker),
            vcp_score=self._series_value(frame.vcp_score, ticker),
            roe_turnaround_score=self._series_value(frame.roe_turnaround_score, ticker),
            insider_score=self._series_value(frame.insider_score, ticker),
            financial_stability_score=self._series_value(frame.financial_stability_score, ticker),
            factor_tags=list(bayes.factor_tags or []),
            posterior_up_prob=safe_probability(bayes.posterior_up_prob, settings.prior_up_prob),
            posterior_up_prob_pct=safe_unit_score(bayes.posterior_up_prob_pct / 100.0) * 100,
            rank=rank,
            as_of=frame.as_of.date(),
        )

    def _build_rows(self, market: str, tickers: list[str], warnings: list[str]) -> list[ScreenerRow]:
        try:
            frame = self.pipeline.run(tickers, market)
        except Exception as exc:
            logger.exception("Factor pipeline failed")
            warnings.append(
                f"데이터 수집 중 오류가 발생해 빈 결과를 반환합니다. ({exc.__class__.__name__})"
            )
            return []

        try:
            names = self.pykrx.get_names(tickers)
        except Exception:
            logger.exception("Ticker name lookup failed")
            names = {ticker: ticker for ticker in tickers}

        rows: list[ScreenerRow] = []
        for ticker in tickers:
            try:
                bayes = self._evaluate(frame, ticker)
                rows.append(
                    self._row_from_frame(
                        frame, ticker, names.get(ticker, ticker), market, bayes, 0
                    )
                )
            except Exception:
                logger.exception("Skipping ticker %s due to row build failure", ticker)
                continue

        if not rows and tickers:
            warnings.append("종목 데이터를 처리하지 못했습니다. KRX/pykrx 연결 상태를 확인하세요.")

        rows.sort(key=lambda r: r.posterior_up_prob, reverse=True)
        return [row.model_copy(update={"rank": idx}) for idx, row in enumerate(rows, start=1)]

    def get_screener(
        self,
        market: str = "KOSPI",
        min_prob: float | None = None,
        limit: int | None = None,
    ) -> ScreenerResponse:
        warnings: list[str] = []
        try:
            tickers = self._resolve_tickers(market, limit)
            if not tickers:
                warnings.append("조회 가능한 종목이 없습니다. fallback 유니버스를 확인하세요.")
                return ScreenerResponse(
                    market=market,
                    as_of=date.today(),
                    count=0,
                    rows=[],
                    warnings=warnings,
                )

            rows = self._build_rows(market, tickers, warnings)
            if min_prob is not None:
                rows = [r for r in rows if r.posterior_up_prob >= min_prob]
            as_of = rows[0].as_of if rows else date.today()
            return ScreenerResponse(
                market=market,
                as_of=as_of,
                count=len(rows),
                rows=rows,
                warnings=warnings,
            )
        except Exception as exc:
            logger.exception("Screener request failed")
            warnings.append(
                f"스크리닝 처리 중 예기치 않은 오류가 발생했습니다. ({exc.__class__.__name__})"
            )
            return ScreenerResponse(
                market=market,
                as_of=date.today(),
                count=0,
                rows=[],
                warnings=warnings,
            )

    def _build_breakdown(self, row: ScreenerRow, bayes) -> list[FactorBreakdown]:
        raw_map = {
            "revision_momentum": row.eps_revision_pct,
            "flow_turnaround": None,
            "vcp_breakout": None,
            "roe_turnaround": row.pbr,
            "insider_buying": None,
            "financial_stability": None,
        }
        breakdown: list[FactorBreakdown] = []
        for key, active in bayes.factors.items():
            score_key = FACTOR_SCORE_KEYS[key]
            score = getattr(row, score_key)
            lr = bayes.likelihood_ratios[key]
            contrib = bayes.log_odds_contributions.get(key, math.log(lr))
            weight = CORE_FACTOR_WEIGHTS.get(key)
            if key not in CORE_FACTOR_WEIGHTS and active:
                weight = settings.auxiliary_bonus_weight
            breakdown.append(
                FactorBreakdown(
                    factor=FACTOR_TAG_LABELS.get(key, key),
                    raw_value=raw_map.get(key),
                    active=active,
                    score=score,
                    weight=weight,
                    likelihood_ratio=lr,
                    logit_contribution=contrib if math.isfinite(contrib) else 0.0,
                )
            )
        return breakdown

    def get_stock_detail(self, ticker: str, market: str = "KOSPI") -> StockDetailResponse | None:
        try:
            frame = self.pipeline.run([ticker], market)
            names = self.pykrx.get_names([ticker])
            bayes = self._evaluate(frame, ticker)
            row = self._row_from_frame(
                frame, ticker, names.get(ticker, ticker), market, bayes, 1
            )
            return StockDetailResponse(
                row=row,
                prior_up_prob=safe_probability(bayes.prior_up_prob, settings.prior_up_prob),
                prior_odds=bayes.prior_odds if math.isfinite(bayes.prior_odds) else self._prior_odds,
                posterior_odds=bayes.posterior_odds if math.isfinite(bayes.posterior_odds) else self._prior_odds,
                breakdown=self._build_breakdown(row, bayes),
            )
        except Exception:
            logger.exception("Stock detail failed for %s", ticker)
            return None
