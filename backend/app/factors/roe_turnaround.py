from __future__ import annotations

from typing import Sequence

import numpy as np

from app.config import settings


def factor_roe_turnaround(
    pbr: float | None,
    current_roe: float | None,
    previous_roe: float | None,
    universe_pbr: Sequence[float],
    *,
    pbr_percentile: float | None = None,
) -> bool:
    """
    ROE 턴어라운드 + 저 PBR: 밸류 트랩 회피를 위해 PBR 하위 + ROE 개선 동시 충족.
    """
    pct = pbr_percentile if pbr_percentile is not None else settings.low_pbr_percentile
    valid_pbr = [float(x) for x in universe_pbr if x is not None and float(x) > 0]
    if pbr is None or float(pbr) <= 0 or not valid_pbr:
        return False
    if current_roe is None or previous_roe is None:
        return False

    threshold = float(np.percentile(valid_pbr, pct * 100))
    low_pbr = float(pbr) <= threshold
    roe_improving = float(current_roe) > float(previous_roe)

    return low_pbr and roe_improving
