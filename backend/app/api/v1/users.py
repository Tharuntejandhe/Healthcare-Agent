"""Self-service data-rights endpoints for the authenticated user.

Supports the controls a health app needs around a patient's own data:
- export everything we hold (HIPAA Right of Access, 45 CFR 164.524)
- delete the account and purge all PHI (files + FAISS index + metadata)
- change password (invalidates other sessions)
- view recent access/activity on the account (transparency)
"""
import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.limits import AUTH_LIMIT, limiter
from app.models.user import User
from app.services import storage
from app.services.audit import record_event
from app.services.ai.rag import delete_user_index, get_all_documents

logger = logging.getLogger("app.api.users")
router = APIRouter()


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


@router.get("/me/export")
async def export_my_data(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Export everything the system holds about the caller (Right of Access)."""
    docs = crud.crud_document.list_for_user(db, user_id=current_user.id)
    indexed_text = await run_in_threadpool(get_all_documents, current_user.id)
    record_event(
        db, action="data.export", resource_type="account",
        user_id=current_user.id, request=request,
    )
    return {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "auth_provider": current_user.auth_provider,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "documents": [
            {
                "filename": d.filename,
                "blob_name": d.blob_name,
                "chunks_indexed": d.chunks_indexed,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "indexed_report_text": None if "No patient reports" in (indexed_text or "") else indexed_text,
    }


@router.get("/me/activity")
def my_activity(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Recent access/activity on the account (transparency for the user)."""
    events = crud.crud_audit.list_for_user(db, user_id=current_user.id, limit=100)
    return {
        "events": [
            {
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "status": e.status,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


@router.post("/me/password")
@limiter.limit(AUTH_LIMIT)
def change_password(
    request: Request,
    body: PasswordChangeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Change the password, invalidate other sessions, return a fresh token."""
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account signs in with Google and has no password to change.",
        )
    if not security.verify_password(body.current_password, current_user.hashed_password):
        record_event(
            db, action="auth.password_change", resource_type="auth",
            user_id=current_user.id, status="denied", request=request,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    user = crud.crud_user.set_password(db, user=current_user, new_password=body.new_password)
    record_event(
        db, action="auth.password_change", resource_type="auth",
        user_id=user.id, request=request,
    )
    # Issue a new token so the current client stays logged in (its old one is now stale).
    token = security.create_access_token(
        user.id,
        token_version=user.token_version,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"message": "Password changed. Other sessions were signed out.", "access_token": token, "token_type": "bearer"}


@router.delete("/me")
async def delete_my_account(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Permanently delete the account and purge all PHI (files + index + metadata)."""
    user_id = current_user.id
    # Record the deletion BEFORE removing the row (the audit log is a retained
    # compliance record and keeps only the user id, never PHI).
    record_event(db, action="account.delete", resource_type="account", user_id=user_id, request=request)

    await run_in_threadpool(storage.delete_all_for_user, user_id)
    await run_in_threadpool(delete_user_index, user_id)
    crud.crud_document.delete_all_for_user(db, user_id=user_id)
    crud.crud_user.delete(db, user=current_user)
    return {"message": "Your account and all associated data have been permanently deleted."}
