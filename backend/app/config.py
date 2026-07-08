from __future__ import annotations

import json
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_origin_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().rstrip("/") for item in value if str(item).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("["):
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ORIGINS JSON must be a list")
            return [str(item).strip().rstrip("/") for item in parsed if str(item).strip()]
        return [part.strip().rstrip("/") for part in raw.split(",") if part.strip()]
    raise ValueError("CORS_ORIGINS must be a comma-separated string or JSON list")


_DEFAULT_LOCAL_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "KOSPI Bayesian Factor Screener"
    debug: bool = True

    # Comma-separated or JSON list. Example (Render/Vercel):
    # CORS_ORIGINS=https://my-app.vercel.app,https://my-app-git-main.vercel.app
    cors_origins: list[str] = _DEFAULT_LOCAL_ORIGINS.copy()

    # Optional single frontend URL (also added to CORS allowlist)
    frontend_url: str | None = None

    # Optional regex for preview deployments, e.g. https://.*\.vercel\.app
    cors_origin_regex: str | None = None

    default_market: str = "KOSPI"
    universe_limit: int = 50
    prior_up_prob: float = 0.52

    flow_short_window: int = 5
    flow_long_window: int = 20
    volume_surge_multiple: float = 3.0
    vcp_lookback_days: int = 126
    bb_window: int = 20
    low_pbr_percentile: float = 0.40
    revision_ratio_threshold: float = 0.03
    earnings_surprise_threshold: float = 0.0
    auxiliary_bonus_weight: float = 0.12

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        parsed = _parse_origin_list(value)
        return parsed if parsed else _DEFAULT_LOCAL_ORIGINS.copy()

    @field_validator("frontend_url", mode="before")
    @classmethod
    def normalize_frontend_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip().rstrip("/")
        return text or None

    @model_validator(mode="after")
    def merge_frontend_url_into_cors(self) -> Settings:
        if self.frontend_url and self.frontend_url not in self.cors_origins:
            self.cors_origins = [*self.cors_origins, self.frontend_url]
        self.cors_origins = list(dict.fromkeys(self.cors_origins))
        return self


settings = Settings()
