"""Centralized exception handlers producing a consistent error shape.

All errors are returned as:
    { "error": { "code": "<machine_code>", "message": "<human readable>", "request_id": "<id>" } }

In production, unexpected exceptions are returned with an opaque message so
internal details don't leak to clients; full stack traces still land in logs.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import request_id_ctx

logger = logging.getLogger("app.errors")


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    extra: dict | None = None,
) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_ctx.get(),
        }
    }
    if extra:
        body["error"].update(extra)
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException):
        code = (
            "not_found"
            if exc.status_code == 404
            else "unauthorized"
            if exc.status_code == 401
            else "forbidden"
            if exc.status_code == 403
            else "bad_request"
            if 400 <= exc.status_code < 500
            else "server_error"
        )
        return _error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc_handler(request: Request, exc: RequestValidationError):
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            message="Request validation failed.",
            extra={"details": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def _unhandled_exc_handler(request: Request, exc: Exception):
        logger.exception("unhandled exception")
        message = (
            "An internal error occurred."
            if settings.is_production
            else f"{type(exc).__name__}: {exc}"
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message=message,
        )
