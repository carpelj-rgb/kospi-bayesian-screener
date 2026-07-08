from datetime import date

from app.config import settings
from app.data.providers.cache import cache_key, get_or_fetch
from app.data.providers.krx_config import get_stock_module, should_use_pykrx

# KRX API 장애 시 사용하는 KOSPI 대표 종목 (시가총액 상위)
FALLBACK_KOSPI_TICKERS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "373220",  # LG에너지솔루션
    "207940",  # 삼성바이오로직스
    "005380",  # 현대차
    "005490",  # POSCO홀딩스
    "035420",  # NAVER
    "000270",  # 기아
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "035720",  # 카카오
    "105560",  # KB금융
    "055550",  # 신한지주
    "032830",  # 삼성생명
    "003670",  # 포스코퓨처엠
    "086790",  # 하나금융지주
    "015760",  # 한국전력
    "010130",  # 고려아연
    "034020",  # 두산에너빌리티
    "009150",  # 삼성전기
]

FALLBACK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "373220": "LG에너지솔루션",
    "207940": "삼성바이오로직스",
    "005380": "현대차",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "000270": "기아",
    "051910": "LG화학",
    "006400": "삼성SDI",
    "035720": "카카오",
    "105560": "KB금융",
    "055550": "신한지주",
    "032830": "삼성생명",
    "003670": "포스코퓨처엠",
    "086790": "하나금융지주",
    "015760": "한국전력",
    "010130": "고려아연",
    "034020": "두산에너빌리티",
    "009150": "삼성전기",
}


def _fetch_tickers(market: str) -> tuple[list[str], bool]:
    if not should_use_pykrx():
        return FALLBACK_KOSPI_TICKERS.copy(), True

    try:
        stock = get_stock_module()
        tickers = stock.get_market_ticker_list(market=market)
        if tickers:
            return tickers, False
    except Exception:
        pass

    return FALLBACK_KOSPI_TICKERS.copy(), True


def get_tickers(market: str = "KOSPI") -> tuple[list[str], bool]:
    """Return tickers and whether fallback universe was used."""
    market_upper = market.upper()
    today = date.today()

    if settings.snapshot_enabled:
        from app.db.snapshot_store import get_snapshot_store

        snapshot = get_snapshot_store().load_universe(market_upper, today)
        if snapshot is not None:
            return snapshot.tickers, snapshot.used_fallback

    key = cache_key("universe", market_upper, today.isoformat())
    tickers, used_fallback = get_or_fetch(key, lambda: _fetch_tickers(market_upper))

    if settings.snapshot_enabled:
        from app.db.snapshot_store import get_snapshot_store

        get_snapshot_store().save_universe(market_upper, tickers, used_fallback, today)

    return tickers, used_fallback


def get_ticker_name(ticker: str) -> str:
    if not should_use_pykrx():
        return FALLBACK_NAMES.get(ticker, ticker)

    key = cache_key("ticker_name", ticker)
    return get_or_fetch(key, lambda: _lookup_ticker_name(ticker))


def _lookup_ticker_name(ticker: str) -> str:
    try:
        stock = get_stock_module()
        name = stock.get_market_ticker_name(ticker)
        if name:
            return name
    except Exception:
        pass
    return FALLBACK_NAMES.get(ticker, ticker)
