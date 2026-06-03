import base64
import logging

from groq import Groq

from app.core.config import settings

logger = logging.getLogger("app.ai.vision")

PROMPT = """
You are a medical AI assistant. Analyze the uploaded image of an injury or body part.
1. Identify the possible nature of the injury (e.g., cut, bruise, rash, burn).
2. Provide a brief contextual description of what is visible.
3. Suggest immediate first aid steps if applicable.

IMPORTANT: Include a medical disclaimer that this is not a professional diagnosis.
"""


OCR_PROMPT = """You are an OCR + medical data extraction engine. The image is a
medical or lab report (it may be a phone photo, a scan, or handwritten).

Transcribe ALL clinically relevant content VERBATIM. For each test/result output
one line in the form:
  <Test name>: <value> <unit> (reference range if shown)
Also include any diagnoses, medications, dates, and notes, one per line.

Rules:
- Output PLAIN TEXT only — no markdown, no commentary, no disclaimer.
- Do NOT invent values. If something is illegible, write it as "[illegible]".
- If the image is clearly NOT a medical/health document, output exactly: NOT_A_REPORT
"""


def _image_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def extract_report_text(image_bytes: bytes, filename: str) -> str:
    """OCR a report photo via the Groq vision model. Returns transcribed text.

    Used when a user uploads a *photo* of their report instead of a PDF (e.g. a
    phone snapshot or a handwritten lab slip). Raises on API failure.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = Groq(
        api_key=settings.GROQ_API_KEY,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )
    mime = _image_mime(image_bytes)
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64_image}"}},
                    ],
                }
            ],
            temperature=0.0,
            max_tokens=2048,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception:
        logger.exception("report OCR failed")
        raise


GENERAL_PROMPT = """You are a medical AI assistant. Look at this medical image and respond appropriately to its type:
- If it is a LAB or MEDICAL REPORT (typed or handwritten): transcribe and summarize the key test names, values, units, reference ranges, and call out any abnormal/critical findings or impressions.
- If it is a photo of an INJURY, skin condition, rash, or body part: describe what is visible, the likely nature, and sensible first-aid steps.
Be factual and concise. Never invent values. A safety disclaimer is added separately."""


def analyze_medical_image(image_bytes: bytes, filename: str) -> str:
    """General-purpose analysis of a medical image — report OR injury.

    Used by the chat attachment flow, where the user may send either a report
    photo or an injury photo. Raises on API failure.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = Groq(
        api_key=settings.GROQ_API_KEY,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )
    mime = _image_mime(image_bytes)
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": GENERAL_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64_image}"}},
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception:
        logger.exception("medical image analysis failed")
        raise


def analyze_injury_image(image_bytes: bytes, filename: str) -> str:
    """Analyze an injury image via Groq's vision model.

    Raises on failure so the caller can return a clean error response rather
    than surfacing an error string as if it were a medical analysis.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = Groq(
        api_key=settings.GROQ_API_KEY,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception:
        logger.exception("vision analysis failed")
        raise
