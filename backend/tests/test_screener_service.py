from unittest.mock import MagicMock

import pandas as pd

from app.factors.models import TickerFactorInputs
from app.services.screener_service import ScreenerService


def _mock_inputs() -> TickerFactorInputs:
    return TickerFactorInputs(
        pbr=0.8,
        universe_pbr=[0.8, 1.2, 2.0],
        net_revision_ratio=0.05,
        earnings_surprise_pct=0.03,
        inst_net_daily=[1, 2, 3, 4, 5],
        combined_net_daily=[-1] * 20 + [1, 2, 3, 4, 5],
        trading_values=[100.0] * 15 + [900.0] * 5,
        closes=[100.0] * 130,
        opens=[99.0] * 130,
        volumes=[1000.0] * 130,
        current_roe=12.0,
        previous_roe=10.0,
        insider_open_market_buy=True,
        debt_ratio=0.3,
        universe_debt_ratios=[0.3, 0.5, 0.8],
        operating_cash_flows_3y=[100.0, 120.0, 140.0],
    )


def test_screener_service_returns_factor_tags():
    inputs = _mock_inputs()
    pipeline = MagicMock()
    pipeline.run.return_value = MagicMock(
        tickers=["005930", "000660"],
        prices=pd.Series({"005930": 70000.0, "000660": 200000.0}),
        pbr=pd.Series({"005930": 0.8, "000660": 2.5}),
        eps_revision_pct=pd.Series({"005930": 5.0, "000660": -2.0}),
        revision_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        flow_turnaround_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        vcp_score=pd.Series({"005930": 0.0, "000660": 0.0}),
        roe_turnaround_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        insider_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        financial_stability_score=pd.Series({"005930": 1.0, "000660": 0.0}),
        factor_inputs={"005930": inputs, "000660": inputs},
        as_of=pd.Timestamp("2026-07-08"),
    )
    pykrx = MagicMock()
    pykrx.get_names.return_value = {"005930": "삼성전자", "000660": "SK하이닉스"}

    response = ScreenerService(pipeline=pipeline, pykrx=pykrx).get_screener(limit=2)
    assert response.count == 2
    assert isinstance(response.rows[0].factor_tags, list)
    assert 0.0 <= response.rows[0].posterior_up_prob_pct <= 100.0


def test_screener_service_tolerates_nan_scores():
    inputs = _mock_inputs()
    pipeline = MagicMock()
    pipeline.run.return_value = MagicMock(
        tickers=["005930"],
        prices=pd.Series({"005930": float("nan")}),
        pbr=pd.Series({"005930": float("nan")}),
        eps_revision_pct=pd.Series({"005930": float("nan")}),
        revision_score=pd.Series({"005930": float("nan")}),
        flow_turnaround_score=pd.Series({"005930": float("nan")}),
        vcp_score=pd.Series({"005930": 0.0}),
        roe_turnaround_score=pd.Series({"005930": 0.0}),
        insider_score=pd.Series({"005930": 0.0}),
        financial_stability_score=pd.Series({"005930": 0.0}),
        factor_inputs={"005930": inputs},
        as_of=pd.Timestamp("2026-07-08"),
    )
    pykrx = MagicMock()
    pykrx.get_names.return_value = {"005930": "삼성전자"}

    response = ScreenerService(pipeline=pipeline, pykrx=pykrx).get_screener(limit=1)
    assert response.count == 1
    assert response.rows[0].revision_score == 0.0
    assert response.rows[0].price is None


def test_screener_service_returns_empty_on_pipeline_failure():
    pipeline = MagicMock()
    pipeline.run.side_effect = RuntimeError("pykrx down")
    pykrx = MagicMock()

    response = ScreenerService(pipeline=pipeline, pykrx=pykrx).get_screener(limit=5)
    assert response.count == 0
    assert response.rows == []
    assert response.warnings


def test_stock_detail_breakdown_has_six_factors():
    inputs = _mock_inputs()
    pipeline = MagicMock()
    pipeline.run.return_value = MagicMock(
        tickers=["005930"],
        prices=pd.Series({"005930": 70000.0}),
        pbr=pd.Series({"005930": 0.8}),
        eps_revision_pct=pd.Series({"005930": 4.0}),
        revision_score=pd.Series({"005930": 1.0}),
        flow_turnaround_score=pd.Series({"005930": 1.0}),
        vcp_score=pd.Series({"005930": 1.0}),
        roe_turnaround_score=pd.Series({"005930": 1.0}),
        insider_score=pd.Series({"005930": 1.0}),
        financial_stability_score=pd.Series({"005930": 1.0}),
        factor_inputs={"005930": inputs},
        as_of=pd.Timestamp("2026-07-08"),
    )
    pykrx = MagicMock()
    pykrx.get_names.return_value = {"005930": "삼성전자"}

    detail = ScreenerService(pipeline=pipeline, pykrx=pykrx).get_stock_detail("005930")
    assert detail is not None
    assert len(detail.breakdown) == 6
