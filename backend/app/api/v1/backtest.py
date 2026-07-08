from fastapi import APIRouter, Depends

from app.api.deps import get_backtest_service
from app.api.query_params import (
    BacktestEndDateParam,
    BacktestMarketParam,
    BacktestStartDateParam,
    BacktestTopNParam,
)
from app.schemas.backtest import BacktestResponse
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest")


@router.get("", response_model=BacktestResponse)
def run_backtest_endpoint(
    market: BacktestMarketParam = "KOSPI",
    top_n: BacktestTopNParam = 10,
    start_date: BacktestStartDateParam = None,
    end_date: BacktestEndDateParam = None,
    service: BacktestService = Depends(get_backtest_service),
) -> BacktestResponse:
    return service.get_backtest(
        market=market,
        top_n=top_n,
        start_date=start_date,
        end_date=end_date,
    )
