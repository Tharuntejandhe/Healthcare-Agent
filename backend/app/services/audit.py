"""Thin helper for writing PHI-access audit events from request handlers.

Audit writes must never break the request they describe: any failure is logged
and swallowed (on its own session rollback) rather than propagated.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app import crud
from app.core.logging import request_id_ctx

logger = logging.getLogger("app.audit")


def record_event(
    db: Session,
    *,
    action: str,
    resource_type: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    request: Optional[Request] = None,
    detail: Optional[str] = None,
) -> None:
    try:
        ip = None
        if request is not None and request.client is not None:
            ip = request.client.host
        crud.crud_audit.create(
            db,
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            status=status,
            ip_address=ip,
            request_id=request_id_ctx.get(),
            detail=detail,
        )
    except Exception:  # pragma: no cover - audit must not break the request
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("failed to write audit event action=%s user=%s", action, user_id)
