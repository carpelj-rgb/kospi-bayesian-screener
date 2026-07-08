import pytest

from run import DEFAULT_PORT, main


def test_default_port_is_render_compatible():
    assert DEFAULT_PORT == "10000"


def test_main_reads_port_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PORT", "12345")
    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr("run.uvicorn.run", fake_run)
    main()
    assert captured["app"] == "app.main:app"
    assert captured["port"] == 12345
    assert captured["host"] == "0.0.0.0"
