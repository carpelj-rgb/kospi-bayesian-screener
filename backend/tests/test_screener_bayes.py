import pytest

from app.bayesian.screener import (
    CORE_FACTOR_WEIGHTS,
    evaluate_screener_posterior,
    evaluate_factor_flags,
    build_factor_tags,
    compute_weighted_log_odds,
    set_prior_odds,
)
from app.factors.financial_stability import factor_financial_stability
from app.factors.flow_turnaround import factor_flow_turnaround
from app.factors.insider_buying import factor_insider_buying
from app.factors.models import TickerFactorInputs
from app.factors.revision_momentum import factor_revision_momentum
from app.factors.roe_turnaround import factor_roe_turnaround


def _base_inputs(**kwargs) -> TickerFactorInputs:
    defaults = dict(
        pbr=1.0,
        universe_pbr=[0.8, 1.0, 1.5, 2.0],
        net_revision_ratio=0.05,
        earnings_surprise_pct=0.02,
        inst_net_daily=[1, 2, 3, 4, 5],
        combined_net_daily=[-1] * 20 + [1, 2, 3, 4, 5],
        trading_values=[100.0] * 15 + [900.0] * 5,
        closes=[100 + i * 0.1 for i in range(130)],
        opens=[99 + i * 0.1 for i in range(130)],
        volumes=[1000.0] * 129 + [2500.0],
        current_roe=12.0,
        previous_roe=10.0,
        insider_stake_increased=False,
        insider_open_market_buy=False,
        debt_ratio=0.3,
        universe_debt_ratios=[0.3, 0.5, 0.8, 1.2],
        operating_cash_flows_3y=[100.0, 120.0, 140.0],
    )
    defaults.update(kwargs)
    return TickerFactorInputs(**defaults)


def test_core_factor_weights_sum_to_one():
    assert sum(CORE_FACTOR_WEIGHTS.values()) == pytest.approx(1.0)


def test_factor_insider_buying():
    assert factor_insider_buying(True, False) is True
    assert factor_insider_buying(False, True) is True
    assert factor_insider_buying(False, False) is False


def test_factor_financial_stability():
    assert factor_financial_stability(0.3, [0.3, 0.5, 0.8, 1.2], [1, 2, 3]) is True
    assert factor_financial_stability(1.5, [0.3, 0.5, 0.8, 1.2], [1, 2, 3]) is False


def test_evaluate_screener_posterior_has_six_factors():
    inputs = _base_inputs(insider_open_market_buy=True)
    result = evaluate_screener_posterior(inputs, base_up_prob=0.52)
    assert len(result.factors) == 6
    assert len(result.factor_tags) >= 1
    assert 0.0 <= result.posterior_up_prob_pct <= 100.0


def test_auxiliary_bonus_increases_posterior():
    base = evaluate_screener_posterior(_base_inputs(), base_up_prob=0.52)
    boosted = evaluate_screener_posterior(
        _base_inputs(insider_open_market_buy=True, insider_stake_increased=True),
        base_up_prob=0.52,
    )
    assert boosted.posterior_up_prob >= base.posterior_up_prob


def test_build_factor_tags():
    flags = evaluate_factor_flags(_base_inputs(insider_open_market_buy=True))
    tags = build_factor_tags(flags)
    assert "내부자매수" in tags


def test_weighted_log_odds_contributions():
    prior = set_prior_odds(0.52)
    flags = evaluate_factor_flags(_base_inputs())
    log_odds, _, contribs = compute_weighted_log_odds(prior, flags)
    assert "revision_momentum" in contribs
    assert log_odds != pytest.approx(__import__("math").log(prior))
