import logging
import os

from groq import Groq

from app.core.config import settings

logger = logging.getLogger("app.ai.speech")


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio via Groq Whisper. Raises on failure."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = Groq(
        api_key=settings.GROQ_API_KEY,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), audio_file),
                model=settings.GROQ_WHISPER_MODEL,
                response_format="json",
            )
        return transcription.text
    except Exception:
        logger.exception("audio transcription failed")
        raise
