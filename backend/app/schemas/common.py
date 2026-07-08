from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    ready: bool = True
    uptime_seconds: float = 0.0
    cache_enabled: bool = True
    cache_entries: int = 0
