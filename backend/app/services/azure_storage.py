"""Azure Blob helpers (only used when STORAGE_BACKEND=azure).

Synchronous, bytes-based API. Ownership/path checks live in services/storage.py;
these functions assume the caller already validated the blob name.
"""
import logging
from datetime import datetime, timedelta, timezone

from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from app.core.config import settings

logger = logging.getLogger("app.storage.azure")


def _client() -> BlobServiceClient:
    conn = settings.AZURE_STORAGE_CONNECTION_STRING
    if not conn:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set")
    return BlobServiceClient.from_connection_string(conn)


def _sas_url(container_name: str, blob_name: str) -> str:
    conn_dict = dict(
        item.split("=", 1)
        for item in settings.AZURE_STORAGE_CONNECTION_STRING.split(";")
        if "=" in item
    )
    account_name = conn_dict.get("AccountName")
    account_key = conn_dict.get("AccountKey")
    if not account_name or not account_key:
        raise ValueError("Invalid Azure connection string: missing AccountName/AccountKey")

    sas_token = generate_blob_sas(
        account_name=account_name,
        account_key=account_key,
        container_name=container_name,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"


def upload_bytes_to_azure(content: bytes, blob_name: str, content_type: str = "application/pdf") -> str:
    """Upload bytes and return a 2-hour SAS URL."""
    client = _client()
    container = settings.AZURE_CONTAINER_NAME
    container_client = client.get_container_client(container)
    if not container_client.exists():
        client.create_container(container)

    blob_client = client.get_blob_client(container=container, blob=blob_name)
    blob_client.upload_blob(
        content,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type, content_disposition="inline"),
    )
    return _sas_url(container, blob_name)


def delete_blob_from_azure(blob_name: str) -> bool:
    try:
        client = _client()
        client.get_blob_client(container=settings.AZURE_CONTAINER_NAME, blob=blob_name).delete_blob()
        return True
    except Exception:
        logger.exception("azure delete failed for %s", blob_name)
        return False
