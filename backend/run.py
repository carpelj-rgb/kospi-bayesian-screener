"""Production entrypoint for Render/Docker (binds to dynamic PORT)."""

from __future__ import annotations

import logging
import os

import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Render injects PORT (commonly 10000). Local Docker Compose sets PORT=8000.
DEFAULT_PORT = "10000"


def main() -> None:
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    logger.info("Starting uvicorn app.main:app on 0.0.0.0:%s (PORT env=%s)", port, os.environ.get("PORT"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info"),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
