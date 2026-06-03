import functools
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core.config import settings
from app.core.limits import AI_LIMIT, limiter
from app.core.uploads import is_image, is_pdf, read_capped
from app.models.user import User
from app.services import storage
from app.services.audit import record_event
from app.services.ai.rag import get_all_documents, index_document_text, process_and_index_document
from app.services.ai.vision import extract_report_text

logger = logging.getLogger("app.api.documents")
router = APIRouter()


def _image_meta(content: bytes) -> tuple[str, str]:
    """(suffix, content_type) from the image's magic bytes."""
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png", "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp", "image/webp"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif", "image/gif"
    return ".jpg", "image/jpeg"


def _doc_to_dict(doc) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "blob_name": doc.blob_name,
        "url": f"/api/v1/documents/local/{doc.blob_name}"
        if settings.STORAGE_BACKEND != "azure"
        else None,
        "chunks_indexed": doc.chunks_indexed,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("")
async def list_documents(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """List the caller's uploaded reports (source of truth — replaces localStorage)."""
    docs = crud.crud_document.list_for_user(db, user_id=current_user.id)
    return {"documents": [_doc_to_dict(d) for d in docs]}


@router.post("/upload")
@limiter.limit(AI_LIMIT)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Upload a medical report as a **PDF or a photo** (JPEG/PNG/WEBP/GIF).

    PDFs are parsed directly; photos (incl. handwritten / phone snapshots) are
    transcribed with the vision model (OCR) and then indexed for RAG — so a user
    who only has a picture of their report card is fully supported.
    """
    content = await read_capped(file, settings.max_upload_bytes)

    if is_pdf(content):
        kind, suffix, ctype = "pdf", ".pdf", "application/pdf"
    elif is_image(content):
        kind = "image"
        suffix, ctype = _image_meta(content)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file. Upload a PDF, or a clear photo (JPEG/PNG) of your report.",
        )

    # For photos: OCR first so we (a) validate it's actually a report and
    # (b) reuse the extracted text for indexing.
    ocr_text = None
    if kind == "image":
        try:
            ocr_text = await run_in_threadpool(
                extract_report_text, content, file.filename or "report"
            )
        except Exception:
            logger.exception("report OCR failed during upload (user=%s)", current_user.id)
            raise HTTPException(
                status_code=502,
                detail="Could not read the report image. Please try a clearer, well-lit photo.",
            )
        if not ocr_text or ocr_text.strip().upper().startswith("NOT_A_REPORT"):
            raise HTTPException(
                status_code=400,
                detail="That image doesn't look like a medical report. Upload a clear photo of your report (or a PDF).",
            )

    try:
        url, blob_name = await run_in_threadpool(
            functools.partial(storage.save_file, content, current_user.id, suffix=suffix, content_type=ctype)
        )
    except Exception:
        logger.exception("storage failure during upload (user=%s)", current_user.id)
        record_event(
            db, action="document.upload", resource_type="document",
            user_id=current_user.id, status="error", request=request,
        )
        raise HTTPException(status_code=502, detail="Could not store the uploaded document.")

    # Indexing is heavy + synchronous (parse/OCR + FAISS); keep it off the event loop.
    filename = file.filename or ("report.pdf" if kind == "pdf" else "report.jpg")
    try:
        if kind == "pdf":
            chunks_indexed = await run_in_threadpool(process_and_index_document, content, filename, current_user.id)
        else:
            chunks_indexed = await run_in_threadpool(index_document_text, ocr_text, filename, current_user.id)
    except Exception:
        logger.exception("indexing failure during upload (user=%s)", current_user.id)
        chunks_indexed = 0  # the file is stored; indexing can be retried later

    doc = crud.crud_document.create(
        db,
        user_id=current_user.id,
        filename=filename,
        blob_name=blob_name,
        content_type=ctype,
        size_bytes=len(content),
        chunks_indexed=chunks_indexed,
    )
    record_event(
        db, action="document.upload", resource_type="document",
        user_id=current_user.id, resource_id=blob_name, request=request,
        detail=f"kind={kind}",
    )

    return {
        "message": "Report uploaded and indexed successfully"
        if chunks_indexed
        else "Report uploaded; indexing will be retried.",
        "id": doc.id,
        "filename": doc.filename,
        "kind": kind,
        "azure_url": url,
        "blob_name": blob_name,
        "chunks_indexed": chunks_indexed,
        "storage_type": settings.STORAGE_BACKEND,
    }


@router.get("/analytical-report")
async def generate_report(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Generate a health analysis report from all of this user's indexed data."""

    def _build() -> dict:
        from app.services.ai.parser import parse_lab_report_lines
        from app.services.analytical_report import generate_health_summary

        full_context = get_all_documents(user_id=current_user.id)
        if not full_context or "No patient reports" in full_context:
            return {
                "message": "No reports found.",
                "status": "empty",
                "summary": "Please upload your medical reports first to generate a full analysis.",
            }

        aggregated_data = parse_lab_report_lines(full_context.split("\n"))
        if not aggregated_data:
            return {
                "message": "Could not extract structured data from reports.",
                "status": "empty",
                "summary": "The AI could not identify specific test results in your uploaded documents.",
            }

        summary = generate_health_summary(aggregated_data)
        stats = {
            "total_tests": len(aggregated_data),
            "high_values": len([i for i in aggregated_data if i["status"] == "HIGH"]),
            "low_values": len([i for i in aggregated_data if i["status"] == "LOW"]),
            "normal_values": len([i for i in aggregated_data if i["status"] == "NORMAL"]),
        }
        return {"summary": summary, "stats": stats, "aggregated_data": aggregated_data, "status": "success"}

    try:
        result = await run_in_threadpool(_build)
        record_event(
            db, action="report.generate", resource_type="report",
            user_id=current_user.id, request=request,
        )
        return result
    except Exception:
        logger.exception("analytical report failed (user=%s)", current_user.id)
        return {
            "message": "Error generating report.",
            "status": "error",
            "summary": "We encountered an issue generating your analysis. Please try again.",
        }


@router.delete("/{blob_name:path}")
async def delete_document(
    blob_name: str,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Delete a stored document the caller owns (file + metadata row)."""
    await run_in_threadpool(storage.delete, blob_name, current_user.id)
    removed = crud.crud_document.delete_by_blob(db, blob_name=blob_name, user_id=current_user.id)
    record_event(
        db, action="document.delete", resource_type="document",
        user_id=current_user.id, resource_id=blob_name,
        status="success" if removed else "denied", request=request,
    )
    # Idempotent from the client's perspective: the record is meant to be gone.
    return {"message": "Document deleted successfully"}


@router.get("/local/user_{user_id}/{filename}")
async def serve_local_file(
    user_id: int,
    filename: str,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Serve a locally stored document (only to its owner)."""
    if current_user.id != user_id:
        record_event(
            db, action="document.view", resource_type="document",
            user_id=current_user.id, resource_id=f"user_{user_id}/{filename}",
            status="denied", request=request,
        )
        raise HTTPException(status_code=403, detail="Unauthorized access to this document.")
    try:
        path = storage.local_file_path(user_id, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    record_event(
        db, action="document.view", resource_type="document",
        user_id=current_user.id, resource_id=f"user_{user_id}/{filename}", request=request,
    )
    return FileResponse(str(path))
