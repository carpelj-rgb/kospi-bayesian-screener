from app.config import Settings


def test_cors_origins_comma_separated():
    settings = Settings(cors_origins="https://a.vercel.app, https://b.vercel.app")
    assert "https://a.vercel.app" in settings.cors_origins
    assert "https://b.vercel.app" in settings.cors_origins


def test_frontend_url_merged_into_cors():
    settings = Settings(
        cors_origins=["http://localhost:3000"],
        frontend_url="https://prod.vercel.app/",
    )
    assert "https://prod.vercel.app" in settings.cors_origins


def test_cors_origin_regex_optional():
    settings = Settings(cors_origin_regex=r"https://.*\.vercel\.app")
    assert settings.cors_origin_regex == r"https://.*\.vercel\.app"
