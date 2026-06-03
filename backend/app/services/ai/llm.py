import logging
from typing import Optional

from langchain_groq import ChatGroq

from app.core.config import settings

logger = logging.getLogger("app.ai.llm")


def get_llm(model: Optional[str] = None, temperature: float = 0.1) -> ChatGroq:
    """Construct a ChatGroq client with explicit timeout + retry budget.

    A hung upstream must not pin a worker forever, so timeout/max_retries are
    always set from config rather than left as library defaults.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.error("GROQ_API_KEY is not set")
        raise ValueError("GROQ_API_KEY environment variable is not set")

    return ChatGroq(
        groq_api_key=api_key,
        model_name=model or settings.GROQ_MODEL,
        temperature=temperature,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )
