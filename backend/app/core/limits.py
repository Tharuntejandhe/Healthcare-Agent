"""Rate limiting via slowapi.

A single shared Limiter is created here and wired into the app in main.py.
Per-route limits are applied with the @limiter.limit(...) decorator; the
decorated route must accept a `request: Request` (and may accept `response`).

Storage defaults to in-process memory (per worker). For accurate limits across
multiple gunicorn workers, set RATE_LIMIT_STORAGE_URI to a shared backend
(e.g. redis://...).
"""
from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import request_id_ctx

logger = logging.getLogger("app.ratelimit")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    enabled=settings.RATE_LIMIT_ENABLED,
    # headers_enabled=True would require every @limiter.limit route to declare a
    # `response: Response` param (slowapi injects X-RateLimit-* there) — omitting
    # it raised "parameter `response` must be an instance of ... Response" at
    # runtime whenever limiting was enabled. Limits are still fully enforced; we
    # just don't emit the informational headers. Our 429 handler sets Retry-After.
    headers_enabled=False,
)

# Convenience limit strings used as decorators across routers.
AUTH_LIMIT = settings.RATE_LIMIT_AUTH
AI_LIMIT = settings.RATE_LIMIT_AI


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return the app's standard error envelope for 429s."""
    logger.warning("rate limit exceeded: %s", exc.detail)
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Too many requests. Please slow down and try again shortly.",
                "request_id": request_id_ctx.get(),
            }
        },
        headers={"Retry-After": "60"},
    )
