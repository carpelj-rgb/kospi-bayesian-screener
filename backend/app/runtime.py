import time

_started_at = time.monotonic()


def uptime_seconds() -> float:
    return round(time.monotonic() - _started_at, 3)
