from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class AuditLog(Base):
    """Append-only record of access to / actions on PHI.

    HIPAA Security Rule §164.312(b) (Audit Controls) requires recording *who*
    did *what* to *which* ePHI and *when*. We never store the PHI itself here —
    only identifiers (user id, resource type/id), the action, source IP and the
    request id, so the log can be retained long-term without itself becoming PHI.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    action = Column(String, nullable=False, index=True)       # e.g. "document.upload"
    resource_type = Column(String, nullable=True)             # e.g. "document", "risk"
    resource_id = Column(String, nullable=True)               # e.g. blob name
    status = Column(String, nullable=False, default="success")  # success | denied | error
    ip_address = Column(String, nullable=True)
    request_id = Column(String, nullable=True, index=True)
    detail = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
