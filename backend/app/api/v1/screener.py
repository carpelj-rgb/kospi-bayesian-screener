from fastapi import APIRouter, Depends, HTTPException
import logging

from app.api.deps import get_screener_service
from app.api.query_params import (
    ScreenerLimitParam,
    ScreenerMarketParam,
    ScreenerMinProbParam,
)
from app.schemas.screener import ScreenerResponse, StockDetailResponse
from app.services.screener_service import ScreenerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screener")


@router.get("", response_model=ScreenerResponse)
def list_screener(
    market: ScreenerMarketParam = "KOSPI",
    min_prob: ScreenerMinProbParam = None,
    limit: ScreenerLimitParam = None,
    service: ScreenerService = Depends(get_screener_service),
) -> ScreenerResponse:
    return service.get_screener(market=market, min_prob=min_prob, limit=limit)


@router.get("/{ticker}", response_model=StockDetailResponse)
def get_stock_detail(
    ticker: str,
    market: ScreenerMarketParam = "KOSPI",
    service: ScreenerService = Depends(get_screener_service),
) -> StockDetailResponse:
    detail = service.get_stock_detail(ticker=ticker, market=market)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    return detail
