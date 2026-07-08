"""
베이지안 확률 계산 — screener.py 위임 래퍼 (하위 호환).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from app.bayesian.screener import (
    DEFAULT_FACTOR_LRS,
    FactorLikelihoodConfig,
    ScreenerBayesResult,
    evaluate_factor_flags,
    evaluate_screener_posterior,
    likelihood_ratio,
    set_prior_odds,
)
from app.config import settings
from app.factors.models import TickerFactorInputs


def prior_odds_from_universe(
    up_count: int,
    total: int,
    *,
    min_prob: float = 0.01,
    max_prob: float = 0.99,
) -> float:
    if total <= 0:
        return set_prior_odds(settings.prior_up_prob)
    rate = float(min(max(up_count / total, min_prob), max_prob))
    return set_prior_odds(rate)


def prior_odds_from_returns(returns: Sequence[float]) -> float:
    if not returns:
        return set_prior_odds(settings.prior_up_prob)
    up_count = sum(1 for r in returns if r > 0)
    return prior_odds_from_universe(up_count, len(returns))


def odds_to_probability(odds: float) -> float:
    if odds <= 0:
        return 0.0
    return odds / (1.0 + odds)


def compute_posterior_probability(
    prior_odds: float,
    likelihood_ratios: Iterable[float],
) -> float:
    post_odds = prior_odds
    for lr in likelihood_ratios:
        post_odds *= lr
    return odds_to_probability(post_odds)


def compute_posterior_odds(
    prior_odds: float,
    likelihood_ratios: Iterable[float],
) -> float:
    post_odds = prior_odds
    for lr in likelihood_ratios:
        post_odds *= lr
    return post_odds


@dataclass
class BayesCalculationResult:
    prior_up_prob: float
    prior_odds: float
    posterior_odds: float
    posterior_up_prob: float
    posterior_up_prob_pct: float = 0.0
    factor_tags: list[str] = field(default_factory=list)
    factors: dict[str, bool] = field(default_factory=dict)
    likelihood_ratios: dict[str, float] = field(default_factory=dict)
    log_odds_contributions: dict[str, float] = field(default_factory=dict)


def _to_legacy_result(result: ScreenerBayesResult) -> BayesCalculationResult:
    return BayesCalculationResult(
        prior_up_prob=result.prior_up_prob,
        prior_odds=result.prior_odds,
        posterior_odds=result.posterior_odds,
        posterior_up_prob=result.posterior_up_prob,
        posterior_up_prob_pct=result.posterior_up_prob_pct,
        factor_tags=result.factor_tags,
        factors=result.factors,
        likelihood_ratios=result.likelihood_ratios,
        log_odds_contributions=result.log_odds_contributions,
    )


def evaluate_stock_posterior(
    inputs: TickerFactorInputs,
    *,
    prior_odds: float | None = None,
    base_up_prob: float | None = None,
    lr_config: Mapping[str, FactorLikelihoodConfig] | None = None,
) -> BayesCalculationResult:
    result = evaluate_screener_posterior(
        inputs,
        prior_odds=prior_odds,
        base_up_prob=base_up_prob,
        lr_config=lr_config,
    )
    return _to_legacy_result(result)
