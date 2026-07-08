from app.services.screener_service import ScreenerService
from app.services.backtest_service import BacktestService

_screener_service: ScreenerService | None = None
_backtest_service: BacktestService | None = None


def get_screener_service() -> ScreenerService:
    global _screener_service
    if _screener_service is None:
        _screener_service = ScreenerService()
    return _screener_service


def get_backtest_service() -> BacktestService:
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService()
    return _backtest_service
