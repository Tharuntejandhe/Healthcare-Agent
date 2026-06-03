import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.limits import AI_LIMIT, limiter
from app.core.uploads import ensure_image, read_capped
from app.services.audit import record_event
from app.services.ai.disclaimer import ensure_disclaimer
from app.services.ai.vision import analyze_injury_image, analyze_medical_image

logger = logging.getLogger("app.api.vision")
router = APIRouter()


@router.post("/analyze")
@limiter.limit(AI_LIMIT)
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """General medical-image analysis (report OR injury) — used by chat attachments."""
    content = await read_capped(file, settings.max_image_bytes)
    ensure_image(content)

    try:
        result = await run_in_threadpool(analyze_medical_image, content, file.filename or "image")
    except Exception:
        logger.exception("medical image analysis failed (user=%s)", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="Image analysis is temporarily unavailable. Please try again in a moment.",
        )

    record_event(
        db, action="vision.analyze", resource_type="vision",
        user_id=current_user.id, request=request,
    )
    return {"filename": file.filename, "analysis": ensure_disclaimer(result)}


@router.post("/analyze-injury")
@limiter.limit(AI_LIMIT)
async def analyze_injury(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """Upload an image of an injury and get a contextual description."""
    content = await read_capped(file, settings.max_image_bytes)
    ensure_image(content)

    try:
        result = await run_in_threadpool(analyze_injury_image, content, file.filename or "image")
    except Exception:
        logger.exception("injury analysis failed (user=%s)", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="Image analysis is temporarily unavailable. Please try again in a moment.",
        )

    record_event(
        db, action="vision.analyze", resource_type="vision",
        user_id=current_user.id, request=request,
    )
    return {"filename": file.filename, "analysis": ensure_disclaimer(result)}
