from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.api.deps import get_screener_service
from app.schemas.screener import ScreenerResponse, StockDetailResponse
from app.services.screener_service import ScreenerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screener")


@router.get("", response_model=ScreenerResponse)
def list_screener(
    market: str = Query(default="KOSPI"),
    min_prob: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int | None = Query(default=None, ge=1, le=200),
    service: ScreenerService = Depends(get_screener_service),
) -> ScreenerResponse:
    return service.get_screener(market=market, min_prob=min_prob, limit=limit)


@router.get("/{ticker}", response_model=StockDetailResponse)
def get_stock_detail(
    ticker: str,
    market: str = Query(default="KOSPI"),
    service: ScreenerService = Depends(get_screener_service),
) -> StockDetailResponse:
    detail = service.get_stock_detail(ticker=ticker, market=market)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    return detail
