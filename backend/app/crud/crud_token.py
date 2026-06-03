"""CRUD for the JWT revocation denylist."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.token import RevokedToken


def revoke(db: Session, *, jti: str, expires_at: datetime, user_id: int | None = None) -> None:
    """Add a token's jti to the denylist (idempotent)."""
    if not jti:
        return
    if db.get(RevokedToken, jti) is not None:
        return
    db.add(RevokedToken(jti=jti, expires_at=expires_at, user_id=user_id))
    db.commit()


def is_revoked(db: Session, *, jti: str) -> bool:
    if not jti:
        return False
    return db.get(RevokedToken, jti) is not None


def purge_expired(db: Session) -> int:
    """Delete denylist rows whose tokens have already expired."""
    now = datetime.now(timezone.utc)
    deleted = db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete()
    db.commit()
    return deleted
