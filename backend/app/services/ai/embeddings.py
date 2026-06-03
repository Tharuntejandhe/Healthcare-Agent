"""Local embeddings backed by fastembed (ONNX, CPU-only, no API key).

Replaces the previous MockEmbeddings, which returned RANDOM vectors and made
RAG retrieval meaningless (dangerous for a medical app — it fed unrelated lab
lines into clinical advice).

The model (default BAAI/bge-small-en-v1.5, ~130 MB, 384-dim) is downloaded on
first use and cached under DATA_DIR/models. Construction is lazy and guarded so
an import/model failure degrades gracefully to "RAG unavailable" instead of
crashing the whole API.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from langchain_core.embeddings import Embeddings

from app.core.config import settings

logger = logging.getLogger("app.ai.embeddings")

# 384-dim — kept consistent with the old mock so index shapes don't change.
EMBED_DIM = 384


class FastEmbedEmbeddings(Embeddings):
    """LangChain Embeddings adapter over fastembed.TextEmbedding."""

    def __init__(self, model_name: str, cache_dir: str):
        from fastembed import TextEmbedding  # imported lazily

        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [vec.tolist() for vec in self._model.embed(list(texts))]

    def embed_query(self, text: str) -> List[float]:
        return next(iter(self._model.embed([text]))).tolist()


_embeddings: Optional[Embeddings] = None
_init_attempted = False


def get_embeddings() -> Optional[Embeddings]:
    """Return a shared embeddings instance, or None if RAG is unavailable.

    Callers must treat None as "retrieval not available" and skip RAG instead
    of failing the request.
    """
    global _embeddings, _init_attempted
    if not settings.ENABLE_RAG:
        return None
    if _embeddings is not None or _init_attempted:
        return _embeddings

    _init_attempted = True
    try:
        cache_dir = settings.data_path / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _embeddings = FastEmbedEmbeddings(settings.EMBEDDING_MODEL, str(cache_dir))
        logger.info("embeddings ready: %s", settings.EMBEDDING_MODEL)
    except Exception:
        logger.exception("failed to initialize embeddings; RAG will be disabled")
        _embeddings = None
    return _embeddings
