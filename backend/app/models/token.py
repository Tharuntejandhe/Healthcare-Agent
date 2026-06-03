from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class RevokedToken(Base):
    """Server-side JWT denylist for single-session logout.

    A stateless JWT cannot otherwise be invalidated before its `exp`. On logout
    we store the token's `jti`; `get_current_user` rejects any token whose jti is
    listed here. Rows are purged once they pass `expires_at` (the token would be
    rejected on expiry anyway), so the table stays small.
    """

    __tablename__ = "revoked_tokens"

    jti = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
