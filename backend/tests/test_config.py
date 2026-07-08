import pytest

from app.config import Settings, _parse_origin_list, _DEFAULT_LOCAL_ORIGINS


def test_cors_origins_comma_separated():
    settings = Settings(cors_origins="https://a.vercel.app, https://b.vercel.app")
    assert "https://a.vercel.app" in settings.cors_origins
    assert "https://b.vercel.app" in settings.cors_origins


def test_cors_origins_json_list_string():
    settings = Settings(
        cors_origins='["https://a.vercel.app","https://b.vercel.app"]'
    )
    assert "https://a.vercel.app" in settings.cors_origins
    assert "https://b.vercel.app" in settings.cors_origins


def test_cors_origins_empty_string_uses_defaults():
    settings = Settings(cors_origins="")
    assert settings.cors_origins == _DEFAULT_LOCAL_ORIGINS


def test_cors_origins_from_env_var(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://prod.vercel.app,https://preview.vercel.app",
    )
    settings = Settings()
    assert "https://prod.vercel.app" in settings.cors_origins
    assert "https://preview.vercel.app" in settings.cors_origins


def test_cors_origins_invalid_json_falls_back_to_split():
    assert _parse_origin_list("[not-valid-json") == ["not-valid-json"]


def test_frontend_url_merged_into_cors():
    settings = Settings(
        cors_origins=["http://localhost:3000"],
        frontend_url="https://prod.vercel.app/",
    )
    assert "https://prod.vercel.app" in settings.cors_origins


def test_cors_origin_regex_optional():
    settings = Settings(cors_origin_regex=r"https://.*\.vercel\.app")
    assert settings.cors_origin_regex == r"https://.*\.vercel\.app"
