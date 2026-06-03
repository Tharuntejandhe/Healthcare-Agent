"""Pluggable document storage — local disk (default) or Postgres.

By default files are written under DATA_DIR/uploads/user_<id>/<uuid>.pdf.
All blob names are server-generated and every path is confined to the uploads
root, so client input can never traverse outside it.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy import delete as sa_delete

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import DocumentBlob

logger = logging.getLogger("app.storage")


def _user_prefix(user_id: int) -> str:
    return f"user_{user_id}/"


def _safe_local_path(blob_name: str) -> Path:
    """Resolve blob_name under the uploads root, rejecting traversal."""
    base = settings.uploads_path.resolve()
    target = (base / blob_name).resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"path traversal rejected: {blob_name}")
    return target


def save_file(
    content: bytes,
    user_id: int,
    *,
    suffix: str = ".pdf",
    content_type: str = "application/octet-stream",
) -> Tuple[str, str]:
    """Persist a file; returns (url_or_path, blob_name)."""
    blob_name = f"{_user_prefix(user_id)}{uuid.uuid4()}{suffix}"

    if settings.STORAGE_BACKEND == "postgres":
        db = SessionLocal()
        try:
            db_blob = DocumentBlob(
                blob_name=blob_name,
                user_id=user_id,
                content=content,
                content_type=content_type,
            )
            db.add(db_blob)
            db.commit()
        finally:
            db.close()
        return f"/api/v1/documents/local/{blob_name}", blob_name

    target = _safe_local_path(blob_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return f"/api/v1/documents/local/{blob_name}", blob_name


def save_pdf(content: bytes, user_id: int) -> Tuple[str, str]:
    """Back-compat helper: persist a PDF report."""
    return save_file(content, user_id, suffix=".pdf", content_type="application/pdf")


def delete(blob_name: str, user_id: int) -> bool:
    """Delete a blob, enforcing that it belongs to user_id."""
    if not blob_name.startswith(_user_prefix(user_id)):
        logger.warning("ownership check failed: user %s tried to delete %s", user_id, blob_name)
        return False

    if settings.STORAGE_BACKEND == "postgres":
        db = SessionLocal()
        try:
            result = db.execute(
                sa_delete(DocumentBlob).where(
                    DocumentBlob.blob_name == blob_name,
                    DocumentBlob.user_id == user_id,
                )
            )
            db.commit()
            return int(getattr(result, 'rowcount', 0) or 0) > 0
        finally:
            db.close()

    try:
        target = _safe_local_path(blob_name)
    except ValueError:
        return False
    if target.exists():
        try:
            target.unlink()
            return True
        except OSError:
            logger.exception("local delete failed for %s", target)
    return False


def get_postgres_file(blob_name: str, user_id: int) -> Tuple[Optional[bytes], Optional[str]]:
    """Retrieve a file stored in Postgres by blob_name."""
    db = SessionLocal()
    try:
        blob = db.query(DocumentBlob).filter(
            DocumentBlob.blob_name == blob_name,
            DocumentBlob.user_id == user_id,
        ).first()
        if blob:
            file_content: bytes = blob.content  # type: ignore[assignment]
            file_ctype: str = blob.content_type  # type: ignore[assignment]
            return file_content, file_ctype
        return None, None
    finally:
        db.close()


def local_file_path(user_id: int, filename: str) -> Path:
    """Confined path for serving a locally stored file (auth checked by caller)."""
    return _safe_local_path(f"{_user_prefix(user_id)}{filename}")


def delete_all_for_user(user_id: int) -> int:
    """Best-effort removal of every stored file for a user (account deletion)."""
    if settings.STORAGE_BACKEND == "postgres":
        db = SessionLocal()
        try:
            result = db.execute(sa_delete(DocumentBlob).where(DocumentBlob.user_id == user_id))
            db.commit()
            return int(getattr(result, 'rowcount', 0) or 0)
        except Exception:
            db.rollback()
            return 0
        finally:
            db.close()

    user_dir = (settings.uploads_path / f"user_{user_id}").resolve()
    base = settings.uploads_path.resolve()
    if user_dir != base and base not in user_dir.parents:
        return 0
    if not user_dir.exists():
        return 0
    removed = 0
    for child in user_dir.glob("*"):
        try:
            if child.is_file():
                child.unlink()
                removed += 1
        except OSError:
            logger.exception("failed to delete %s", child)
    try:
        user_dir.rmdir()
    except OSError:
        pass
    return removed
