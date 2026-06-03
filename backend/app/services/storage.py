"""Pluggable document storage — local disk (default) or Azure Blob.

This removes the hard Azure dependency: by default files are written under
DATA_DIR/uploads/user_<id>/<uuid>.pdf. All blob names are server-generated and
every path is confined to the uploads root, so client input can never traverse
outside it.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Tuple

from app.core.config import settings

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
    """Persist a file; returns (url_or_path, blob_name).

    blob_name is always "user_<id>/<uuid><suffix>" (server-generated, so client
    input can never traverse). For local storage the url is the authenticated
    serving route; for Azure it is a short-lived SAS URL.
    """
    blob_name = f"{_user_prefix(user_id)}{uuid.uuid4()}{suffix}"

    if settings.STORAGE_BACKEND == "azure":
        from app.services.azure_storage import upload_bytes_to_azure

        url = upload_bytes_to_azure(content, blob_name, content_type)
        return url, blob_name

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

    if settings.STORAGE_BACKEND == "azure":
        from app.services.azure_storage import delete_blob_from_azure

        return delete_blob_from_azure(blob_name)

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


def local_file_path(user_id: int, filename: str) -> Path:
    """Confined path for serving a locally stored file (auth checked by caller)."""
    return _safe_local_path(f"{_user_prefix(user_id)}{filename}")


def delete_all_for_user(user_id: int) -> int:
    """Best-effort removal of every stored file for a user (account deletion).

    Returns the number of files removed. Storage cleanup must not block the
    deletion of the user's database records, so failures are logged, not raised.
    """
    if settings.STORAGE_BACKEND == "azure":
        try:
            from app.services.azure_storage import delete_prefix_from_azure

            return delete_prefix_from_azure(_user_prefix(user_id))
        except Exception:
            logger.exception("azure purge failed for user %s", user_id)
            return 0

    user_dir = (settings.uploads_path / f"user_{user_id}").resolve()
    base = settings.uploads_path.resolve()
    # Defensive: never delete outside the uploads root.
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
