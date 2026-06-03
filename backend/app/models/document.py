from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class Document(Base):
    """Metadata for an uploaded patient report.

    The file bytes live in storage (local disk or Azure); this row is the
    authoritative record of *which* user owns *which* blob, the original file
    name, and how many RAG chunks were indexed. It replaces the previous
    approach of keeping the report list in browser localStorage (which exposed
    PHI to any XSS) and is the source of truth for listing, export and deletion.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    filename = Column(String, nullable=False)             # original client filename
    blob_name = Column(String, unique=True, index=True, nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    chunks_indexed = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
