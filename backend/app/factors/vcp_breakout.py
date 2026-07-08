from __future__ import annotations

import numpy as np

from app.config import settings


def _bollinger_bandwidth(closes: np.ndarray, window: int) -> np.ndarray:
    if len(closes) < window:
        return np.array([])
    bandwidths: list[float] = []
    for i in range(window - 1, len(closes)):
        segment = closes[i - window + 1 : i + 1]
        sma = float(segment.mean())
        std = float(segment.std(ddof=0))
        if sma <= 0:
            bandwidths.append(np.nan)
            continue
        upper = sma + 2 * std
        lower = sma - 2 * std
        bandwidths.append((upper - lower) / sma)
    return np.array(bandwidths, dtype=float)


def factor_vcp_breakout(
    closes: list[float],
    opens: list[float],
    volumes: list[float],
    *,
    bb_window: int | None = None,
    lookback: int | None = None,
) -> bool:
    """
    VCP: 볼린저 밴드폭 6개월 내 최저 근접 + 상단 밴드 돌파 + 거래량/몸통 동반.
    """
    bb_w = bb_window or settings.bb_window
    lb = lookback or settings.vcp_lookback_days

    if len(closes) < max(lb, bb_w + 5) or len(opens) < len(closes) or len(volumes) < len(closes):
        return False

    c = np.array(closes[-lb:], dtype=float)
    o = np.array(opens[-lb:], dtype=float)
    v = np.array(volumes[-lb:], dtype=float)

    bandwidth = _bollinger_bandwidth(c, bb_w)
    if bandwidth.size == 0 or np.all(np.isnan(bandwidth)):
        return False

    valid_bw = bandwidth[~np.isnan(bandwidth)]
    if valid_bw.size == 0:
        return False

    current_bw = float(valid_bw[-1])
    min_bw = float(np.min(valid_bw))
    squeeze = current_bw <= min_bw * 1.05

    segment = c[-bb_w:]
    sma = float(segment.mean())
    std = float(segment.std(ddof=0))
    upper_band = sma + 2 * std
    breakout = float(c[-1]) > upper_band

    body = abs(float(c[-1]) - float(o[-1]))
    avg_body = float(np.mean(np.abs(c[-bb_w:] - o[-bb_w:])))
    avg_vol = float(np.mean(v[-bb_w:]))
    vol_surge = avg_vol > 0 and float(v[-1]) / avg_vol >= 1.5
    body_ok = avg_body > 0 and body >= avg_body * 0.8

    return squeeze and breakout and vol_surge and body_ok
