"""
베이지안 스크리너 — 가중 Log-Odds 사후확률 계산.

핵심 4팩터 (가중치 합 100%):
  - revision_momentum: 30%
  - roe_turnaround: 25%
  - flow_turnaround: 25%
  - vcp_breakout: 20%

보조 2팩터 (High-LR, 활성 시 log-odds 가산):
  - insider_buying
  - financial_stability
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from app.config import settings
from app.factors.financial_stability import factor_financial_stability
from app.factors.flow_turnaround import factor_flow_turnaround
from app.factors.insider_buying import factor_insider_buying
from app.factors.models import TickerFactorInputs
from app.factors.revision_momentum import factor_revision_momentum
from app.factors.roe_turnaround import factor_roe_turnaround
from app.factors.vcp_breakout import factor_vcp_breakout

FACTOR_TAG_LABELS: Mapping[str, str] = {
    "revision_momentum": "Revision",
    "roe_turnaround": "ROE↑",
    "flow_turnaround": "수급전환",
    "vcp_breakout": "VCP",
    "insider_buying": "내부자매수",
    "financial_stability": "재무안정",
}

CORE_FACTOR_WEIGHTS: Mapping[str, float] = {
    "revision_momentum": 0.30,
    "roe_turnaround": 0.25,
    "flow_turnaround": 0.25,
    "vcp_breakout": 0.20,
}

AUXILIARY_FACTORS: tuple[str, ...] = ("insider_buying", "financial_stability")


@dataclass(frozen=True)
class FactorLikelihoodConfig:
    lr_if_true: float
    lr_if_false: float


DEFAULT_FACTOR_LRS: Mapping[str, FactorLikelihoodConfig] = {
    "revision_momentum": FactorLikelihoodConfig(lr_if_true=2.20, lr_if_false=0.72),
    "flow_turnaround": FactorLikelihoodConfig(lr_if_true=2.50, lr_if_false=0.70),
    "vcp_breakout": FactorLikelihoodConfig(lr_if_true=2.10, lr_if_false=0.75),
    "roe_turnaround": FactorLikelihoodConfig(lr_if_true=1.90, lr_if_false=0.78),
    "insider_buying": FactorLikelihoodConfig(lr_if_true=2.80, lr_if_false=0.85),
    "financial_stability": FactorLikelihoodConfig(lr_if_true=2.40, lr_if_false=0.88),
}


def set_prior_odds(base_up_prob: float) -> float:
    p = float(np.clip(base_up_prob, 0.01, 0.99))
    return p / (1.0 - p)


def likelihood_ratio(active: bool, config: FactorLikelihoodConfig) -> float:
    return config.lr_if_true if active else config.lr_if_false


def evaluate_factor_flags(inputs: TickerFactorInputs) -> dict[str, bool]:
    """6팩터 불리언 평가."""
    return {
        "revision_momentum": factor_revision_momentum(
            inputs.net_revision_ratio,
            inputs.earnings_surprise_pct,
            inputs.inst_net_daily,
        ),
        "flow_turnaround": factor_flow_turnaround(
            inputs.combined_net_daily,
            inputs.trading_values,
        ),
        "vcp_breakout": factor_vcp_breakout(
            inputs.closes,
            inputs.opens,
            inputs.volumes,
        ),
        "roe_turnaround": factor_roe_turnaround(
            inputs.pbr,
            inputs.current_roe,
            inputs.previous_roe,
            inputs.universe_pbr,
        ),
        "insider_buying": factor_insider_buying(
            inputs.insider_stake_increased,
            inputs.insider_open_market_buy,
        ),
        "financial_stability": factor_financial_stability(
            inputs.debt_ratio,
            inputs.universe_debt_ratios or [],
            inputs.operating_cash_flows_3y or [],
        ),
    }


def build_factor_tags(factors: Mapping[str, bool]) -> list[str]:
    """충족된 팩터 태그 리스트."""
    return [FACTOR_TAG_LABELS[key] for key, active in factors.items() if active]


def log_odds_to_probability(log_odds: float) -> float:
    if log_odds != log_odds or log_odds == float("inf"):
        return 1.0
    if log_odds == float("-inf"):
        return 0.0
    odds = math.exp(log_odds)
    if not math.isfinite(odds):
        return 1.0 if odds > 0 else 0.0
    return odds / (1.0 + odds)


def probability_to_pct(probability: float) -> float:
    if probability != probability or probability in (float("inf"), float("-inf")):
        return 0.0
    return round(float(min(1.0, max(0.0, probability))) * 100, 2)


@dataclass
class ScreenerBayesResult:
    prior_up_prob: float
    prior_odds: float
    posterior_odds: float
    posterior_up_prob: float
    posterior_up_prob_pct: float
    factor_tags: list[str]
    factors: dict[str, bool] = field(default_factory=dict)
    likelihood_ratios: dict[str, float] = field(default_factory=dict)
    log_odds_contributions: dict[str, float] = field(default_factory=dict)


def compute_weighted_log_odds(
    prior_odds: float,
    factors: Mapping[str, bool],
    lr_config: Mapping[str, FactorLikelihoodConfig] | None = None,
) -> tuple[float, dict[str, float], dict[str, float]]:
    """
    log(Odds_post) = log(Odds_prior)
                   + Σ w_i · log(LR_i)           [core 4]
                   + Σ bonus · log(LR_aux)       [aux active only]
    """
    lrs = lr_config or DEFAULT_FACTOR_LRS
    log_odds = math.log(prior_odds)
    lr_values: dict[str, float] = {}
    contributions: dict[str, float] = {}

    for name, weight in CORE_FACTOR_WEIGHTS.items():
        lr = likelihood_ratio(factors[name], lrs[name])
        lr_values[name] = lr
        contrib = weight * math.log(lr)
        contributions[name] = contrib
        log_odds += contrib

    bonus = settings.auxiliary_bonus_weight
    for name in AUXILIARY_FACTORS:
        lr_cfg = lrs[name]
        if factors.get(name):
            lr = lr_cfg.lr_if_true
            contrib = bonus * math.log(lr)
        else:
            lr = lr_cfg.lr_if_false
            contrib = 0.0
        lr_values[name] = lr if factors.get(name) else lr_cfg.lr_if_false
        contributions[name] = contrib
        if factors.get(name):
            log_odds += contrib

    return log_odds, lr_values, contributions


def evaluate_screener_posterior(
    inputs: TickerFactorInputs,
    *,
    prior_odds: float | None = None,
    base_up_prob: float | None = None,
    lr_config: Mapping[str, FactorLikelihoodConfig] | None = None,
) -> ScreenerBayesResult:
    """가중 Log-Odds 기반 사후확률 산출."""
    if prior_odds is None:
        prob = base_up_prob if base_up_prob is not None else settings.prior_up_prob
        prior_odds = set_prior_odds(prob)

    factors = evaluate_factor_flags(inputs)
    log_odds, lr_values, contributions = compute_weighted_log_odds(
        prior_odds, factors, lr_config
    )
    posterior_odds = math.exp(log_odds) if math.isfinite(log_odds) else float("inf")
    posterior_prob = log_odds_to_probability(log_odds)

    return ScreenerBayesResult(
        prior_up_prob=log_odds_to_probability(math.log(prior_odds)),
        prior_odds=prior_odds,
        posterior_odds=posterior_odds if math.isfinite(posterior_odds) else float("inf"),
        posterior_up_prob=posterior_prob,
        posterior_up_prob_pct=probability_to_pct(posterior_prob),
        factor_tags=build_factor_tags(factors),
        factors=dict(factors),
        likelihood_ratios=lr_values,
        log_odds_contributions=contributions,
    )
