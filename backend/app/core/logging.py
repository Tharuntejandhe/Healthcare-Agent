"""Structured logging setup with request-scoped context.

In production we emit single-line JSON for log aggregators; in development
we keep a human-readable format. A ContextVar carries a per-request ID so
every log line emitted during a request handler can be correlated.
"""
from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict

from app.core.config import settings

# Per-request ID, set by RequestContextMiddleware. "-" means "no active request".
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter — one record per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Allow ad-hoc structured fields via `logger.info(..., extra={"extra_fields": {...}})`
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_ctx.get()
        base = super().format(record)
        return f"[req={rid}] {base}"


def configure_logging() -> None:
    """Configure the root logger. Idempotent — safe to call on every startup."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(stream=sys.stdout)
    if settings.is_production:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    root = logging.getLogger()
    # Drop any pre-existing handlers (uvicorn installs its own defaults early).
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet down some chatty third-party loggers in production.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if settings.is_production else logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
