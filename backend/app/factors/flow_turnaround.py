from app.config import settings


def factor_flow_turnaround(
    combined_net_daily: list[float],
    trading_values: list[float],
    *,
    long_window: int | None = None,
    short_window: int | None = None,
    volume_surge_multiple: float | None = None,
) -> bool:
    """
    수급 구조적 변화: 20일 순매도 → 5일 연속 외인+기관 순매수 + 거래대금 300% 급증.
    """
    long_w = long_window or settings.flow_long_window
    short_w = short_window or settings.flow_short_window
    surge = volume_surge_multiple or settings.volume_surge_multiple

    if len(combined_net_daily) < long_w + short_w:
        return False

    long_period = combined_net_daily[-(long_w + short_w) : -short_w]
    short_period = combined_net_daily[-short_w:]

    long_net_selling = sum(float(x) for x in long_period) < 0
    streak_reversal = all(float(x) > 0 for x in short_period)

    volume_surge = False
    if len(trading_values) >= long_w:
        avg_short = sum(float(x) for x in trading_values[-short_w:]) / short_w
        avg_long = sum(float(x) for x in trading_values[-long_w:]) / long_w
        if avg_long > 0:
            volume_surge = avg_short >= surge * avg_long

    return long_net_selling and streak_reversal and volume_surge
