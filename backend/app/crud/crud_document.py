"""CRUD for uploaded-document metadata."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.document import Document


def create(
    db: Session,
    *,
    user_id: int,
    filename: str,
    blob_name: str,
    content_type: Optional[str] = None,
    size_bytes: Optional[int] = None,
    chunks_indexed: int = 0,
) -> Document:
    doc = Document(
        user_id=user_id,
        filename=filename,
        blob_name=blob_name,
        content_type=content_type,
        size_bytes=size_bytes,
        chunks_indexed=chunks_indexed,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_for_user(db: Session, *, user_id: int) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_by_blob(db: Session, *, blob_name: str, user_id: int) -> Optional[Document]:
    return (
        db.query(Document)
        .filter(Document.blob_name == blob_name, Document.user_id == user_id)
        .first()
    )


def delete_by_blob(db: Session, *, blob_name: str, user_id: int) -> bool:
    doc = get_by_blob(db, blob_name=blob_name, user_id=user_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


def delete_all_for_user(db: Session, *, user_id: int) -> int:
    deleted = db.query(Document).filter(Document.user_id == user_id).delete()
    db.commit()
    return deleted
