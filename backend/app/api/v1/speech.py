import logging
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.limits import AI_LIMIT, limiter
from app.core.uploads import ensure_audio, read_capped
from app.services.audit import record_event
from app.services.ai.speech import transcribe_audio

logger = logging.getLogger("app.api.speech")
router = APIRouter()


@router.post("/transcribe")
@limiter.limit(AI_LIMIT)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """Upload an audio file and get the text transcript."""
    content = await read_capped(file, settings.max_audio_bytes)
    ensure_audio(content)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        transcript = await run_in_threadpool(transcribe_audio, tmp_path)
        record_event(
            db, action="speech.transcribe", resource_type="speech",
            user_id=current_user.id, request=request,
        )
        return {"transcript": transcript}
    except Exception:
        logger.exception("transcription failed (user=%s)", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="Transcription is temporarily unavailable. Please try again in a moment.",
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
