from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Callable, TypeVar

from app.config import settings

T = TypeVar("T")

_MISSING = object()


class TTLCache:
    """Thread-safe in-memory cache with TTL expiry and LRU eviction."""

    def __init__(self, ttl_seconds: float, max_entries: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._store: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._lock = Lock()

    def _purge_expired(self, now: float) -> None:
        expired = [key for key, (expires_at, _) in self._store.items() if expires_at <= now]
        for key in expired:
            self._store.pop(key, None)

    def get(self, key: str) -> object | type[_MISSING]:
        if not settings.cache_enabled:
            return _MISSING
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            item = self._store.get(key)
            if item is None:
                return _MISSING
            expires_at, value = item
            if expires_at <= now:
                self._store.pop(key, None)
                return _MISSING
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: object) -> None:
        if not settings.cache_enabled:
            return
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            self._store[key] = (now + self.ttl_seconds, value)
            self._store.move_to_end(key)
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            return len(self._store)


_data_cache: TTLCache | None = None


def get_data_cache() -> TTLCache:
    global _data_cache
    if _data_cache is None:
        _data_cache = TTLCache(
            ttl_seconds=float(settings.cache_ttl_seconds),
            max_entries=settings.cache_max_entries,
        )
    return _data_cache


def cache_key(*parts: object) -> str:
    return ":".join(str(part) for part in parts)


def get_or_fetch(key: str, fetcher: Callable[[], T]) -> T:
    cache = get_data_cache()
    cached = cache.get(key)
    if cached is not _MISSING:
        return cached  # type: ignore[return-value]
    value = fetcher()
    cache.set(key, value)
    return value


def cache_stats() -> dict[str, int | bool]:
    return {
        "cache_enabled": settings.cache_enabled,
        "cache_entries": get_data_cache().size,
    }
