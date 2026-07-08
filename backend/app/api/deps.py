from app.services.screener_service import ScreenerService

_screener_service: ScreenerService | None = None


def get_screener_service() -> ScreenerService:
    global _screener_service
    if _screener_service is None:
        _screener_service = ScreenerService()
    return _screener_service
