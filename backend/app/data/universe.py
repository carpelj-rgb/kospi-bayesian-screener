from pykrx import stock

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


def get_tickers(market: str = "KOSPI") -> list[str]:
    try:
        tickers = stock.get_market_ticker_list(market=market)
        if tickers:
            return tickers
    except Exception:
        pass
    if market.upper() == "KOSPI":
        return FALLBACK_KOSPI_TICKERS.copy()
    return FALLBACK_KOSPI_TICKERS.copy()


def get_ticker_name(ticker: str) -> str:
    try:
        name = stock.get_market_ticker_name(ticker)
        if name:
            return name
    except Exception:
        pass
    return FALLBACK_NAMES.get(ticker, ticker)
