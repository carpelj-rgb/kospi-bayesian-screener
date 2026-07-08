from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_pykrx_logging() -> None:
    """Suppress pykrx internal logging bugs (TypeError in logging.info)."""
    for name in ("pykrx", "pykrx.website", "root"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


def should_use_pykrx() -> bool:
    """
    KRX credentials 없으면 pykrx 호출 생략 (Render/cloud에서 로그·지연 방지).
    PYKRX_ENABLED=true 로 명시하면 credentials 없어도 시도.
    """
    flag = os.environ.get("PYKRX_ENABLED")
    if flag is not None:
        return flag.strip().lower() in ("1", "true", "yes", "on")
    return bool(os.environ.get("KRX_ID") and os.environ.get("KRX_PW"))
