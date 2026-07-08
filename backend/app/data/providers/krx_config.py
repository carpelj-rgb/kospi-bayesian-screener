from __future__ import annotations

import io
import logging
import os
from contextlib import redirect_stderr, redirect_stdout
from types import ModuleType
from typing import Literal

logger = logging.getLogger(__name__)

_configured = False
_stock_module: ModuleType | None = None

DataSourceMode = Literal["full", "limited"]
LIMITED_DATA_NOTE = (
    "KRX/pykrx 일부 데이터를 사용하지 못해 제한 모드(fallback 유니버스 + yfinance)로 계산했습니다."
)


def configure_pykrx() -> None:
    """Suppress pykrx internal logging before first use."""
    global _configured
    if _configured:
        return
    _configured = True

    for name in ("pykrx", "pykrx.website", "pykrx.website.comm", "root"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


def should_use_pykrx() -> bool:
    """
    pykrx is enabled by default (public KRX endpoints, no corporate login required).
    Set PYKRX_ENABLED=false to disable pykrx entirely and use fallback + yfinance only.
    """
    flag = os.environ.get("PYKRX_ENABLED")
    if flag is None:
        return True
    return flag.strip().lower() in ("1", "true", "yes", "on")


def get_stock_module():
    """Lazy-load pykrx.stock while silencing startup auth/login messages."""
    global _stock_module
    if _stock_module is None:
        configure_pykrx()
        sink = io.StringIO()
        with redirect_stdout(sink), redirect_stderr(sink):
            from pykrx import stock as loaded

        _stock_module = loaded
    return _stock_module


# Backwards-compatible alias
configure_pykrx_logging = configure_pykrx
