from app.config import settings


def factor_revision_momentum(
    net_revision_ratio: float | None,
    earnings_surprise_pct: float | None,
    inst_net_daily: list[float],
    *,
    revision_threshold: float | None = None,
    surprise_threshold: float | None = None,
    inst_window: int = 5,
) -> bool:
    """
    어닝 서프라이즈 + EPS 컨센서스 상향(Revision Momentum).
    Net Revision Ratio 양(+) AND (서프라이즈 OR 기관 순매수 동반).
    """
    rev_th = revision_threshold if revision_threshold is not None else settings.revision_ratio_threshold
    sur_th = surprise_threshold if surprise_threshold is not None else settings.earnings_surprise_threshold

    revision_ok = net_revision_ratio is not None and float(net_revision_ratio) > rev_th
    surprise_ok = earnings_surprise_pct is not None and float(earnings_surprise_pct) > sur_th

    inst_ok = False
    if len(inst_net_daily) >= inst_window:
        recent = inst_net_daily[-inst_window:]
        inst_ok = all(float(x) > 0 for x in recent)

    return revision_ok and (surprise_ok or inst_ok)
