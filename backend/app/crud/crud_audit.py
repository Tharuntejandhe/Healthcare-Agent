"""CRUD for PHI access audit logs."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def create(
    db: Session,
    *,
    action: str,
    resource_type: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        resource_id=resource_id,
        status=status,
        ip_address=ip_address,
        request_id=request_id,
        detail=detail,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_for_user(db: Session, *, user_id: int, limit: int = 100) -> List[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
