from fastapi import APIRouter, Response

from app.config import settings
from app.data.providers.cache import cache_stats
from app.db.snapshot_store import get_snapshot_store
from app.runtime import uptime_seconds
from app.schemas.common import HealthResponse

router = APIRouter()


def _health_payload() -> HealthResponse:
    stats = cache_stats()
    snapshot_stats = (
        get_snapshot_store().stats()
        if settings.snapshot_enabled
        else {"universe_snapshots": 0, "factor_snapshots": 0}
    )
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        ready=True,
        uptime_seconds=uptime_seconds(),
        cache_enabled=bool(stats["cache_enabled"]),
        cache_entries=int(stats["cache_entries"]),
        snapshot_enabled=settings.snapshot_enabled,
        snapshot_universe_rows=int(snapshot_stats["universe_snapshots"]),
        snapshot_factor_rows=int(snapshot_stats["factor_snapshots"]),
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Lightweight liveness probe for Render/cron pings (no data fetching)."""
    return _health_payload()


@router.head("/health", include_in_schema=False)
def health_head() -> Response:
    """HEAD alias for uptime monitors — empty body, minimal work."""
    return Response(
        status_code=200,
        headers={
            "Cache-Control": "no-store",
            "X-App-Status": "ok",
        },
    )
