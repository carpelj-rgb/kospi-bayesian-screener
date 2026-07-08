import time

import pytest

from app.data.providers.cache import TTLCache, cache_key, get_or_fetch


def test_ttl_cache_hit_and_miss():
    from app.data.providers.cache import _MISSING

    cache = TTLCache(ttl_seconds=60, max_entries=10)
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is _MISSING


def test_ttl_cache_expires():
    cache = TTLCache(ttl_seconds=0.01, max_entries=10)
    cache.set("a", 1)
    time.sleep(0.02)
    from app.data.providers.cache import _MISSING

    assert cache.get("a") is _MISSING


def test_ttl_cache_lru_eviction():
    from app.data.providers.cache import _MISSING

    cache = TTLCache(ttl_seconds=60, max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is _MISSING
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_get_or_fetch_calls_fetcher_once(monkeypatch):
    monkeypatch.setenv("CACHE_ENABLED", "true")
    from app.config import settings

    settings.cache_enabled = True
    from app.data.providers import cache as cache_module

    cache_module._data_cache = TTLCache(ttl_seconds=60, max_entries=10)

    calls = {"n": 0}

    def fetcher():
        calls["n"] += 1
        return "value"

    key = cache_key("test", "key")
    assert get_or_fetch(key, fetcher) == "value"
    assert get_or_fetch(key, fetcher) == "value"
    assert calls["n"] == 1
