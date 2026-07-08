"""재무 안정성 필터: 부채비율 업종(유니버스) 하위 50% + OCF 3년 연속 플러스."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from app.config import settings


def factor_financial_stability(
    debt_ratio: float | None,
    universe_debt_ratios: Sequence[float],
    operating_cash_flows_3y: Sequence[float],
    *,
    debt_percentile: float = 0.50,
    required_years: int = 3,
) -> bool:
    valid_debt = [float(x) for x in universe_debt_ratios if x is not None and float(x) >= 0]
    if debt_ratio is None or not valid_debt:
        return False

    threshold = float(np.percentile(valid_debt, debt_percentile * 100))
    low_debt = float(debt_ratio) <= threshold

    ocf = [float(x) for x in operating_cash_flows_3y if x is not None]
    ocf_positive = len(ocf) >= required_years and all(v > 0 for v in ocf[-required_years:])

    _ = settings
    return low_debt and ocf_positive
