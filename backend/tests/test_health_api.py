from app.api.v1.health import _health_payload


def test_health_payload_includes_uptime_and_cache():
    body = _health_payload()
    assert body.status == "ok"
    assert body.ready is True
    assert body.uptime_seconds >= 0
    assert body.cache_entries >= 0
