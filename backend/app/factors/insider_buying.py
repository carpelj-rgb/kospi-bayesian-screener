"""내부자/최대주주 매수 팩터."""

from app.config import settings


def factor_insider_buying(
    stake_increased: bool,
    open_market_buy: bool,
) -> bool:
    """최대주주·내부자 지분율 증가 또는 장내 매수 공시."""
    _ = settings  # reserved for future thresholds
    return stake_increased or open_market_buy
