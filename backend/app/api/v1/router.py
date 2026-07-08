from fastapi import APIRouter

from app.api.v1 import backtest, health, screener

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(screener.router, tags=["screener"])
router.include_router(backtest.router, tags=["backtest"])
