import pytest

from app.bayesian.bayes_calculator import (
    compute_posterior_probability,
    evaluate_stock_posterior,
    likelihood_ratio,
    prior_odds_from_universe,
    set_prior_odds,
    FactorLikelihoodConfig,
)
from app.factors.flow_turnaround import factor_flow_turnaround
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
    )
    defaults.update(kwargs)
    return TickerFactorInputs(**defaults)


def test_set_prior_odds():
    assert set_prior_odds(0.52) == pytest.approx(0.52 / 0.48, rel=1e-6)


def test_prior_odds_from_universe():
    odds = prior_odds_from_universe(up_count=52, total=100)
    assert odds == pytest.approx(set_prior_odds(0.52), rel=1e-6)


def test_factor_revision_momentum():
    assert factor_revision_momentum(0.05, 0.02, [1, 2, 3, 4, 5]) is True
    assert factor_revision_momentum(0.01, 0.02, [1, 2, 3, 4, 5]) is False


def test_factor_flow_turnaround():
    combined = [-1.0] * 20 + [1.0, 2.0, 3.0, 4.0, 5.0]
    values = [100.0] * 15 + [900.0] * 5
    assert factor_flow_turnaround(combined, values) is True


def test_factor_roe_turnaround():
    universe = [0.5, 0.8, 1.2, 2.0, 3.0]
    assert factor_roe_turnaround(0.5, 12.0, 10.0, universe) is True


def test_likelihood_ratio():
    cfg = FactorLikelihoodConfig(lr_if_true=2.0, lr_if_false=0.5)
    assert likelihood_ratio(True, cfg) == 2.0


def test_evaluate_stock_posterior():
    result = evaluate_stock_posterior(_base_inputs(), base_up_prob=0.52)
    assert len(result.factors) == 6
    assert isinstance(result.factor_tags, list)
    assert 0.0 <= result.posterior_up_prob_pct <= 100.0
