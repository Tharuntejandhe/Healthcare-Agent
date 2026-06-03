"""User-isolated RAG over Neon pgvector, using real local embeddings.

Replaces the previous FAISS implementation with standard Postgres vector operations.
"""
import logging
import os
import tempfile
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from sqlalchemy import text, delete

from app.db.session import SessionLocal
from app.models.document import DocumentChunk
from app.services.ai.embeddings import get_embeddings
from app.services.pdf_processor import extract_text_from_pdf

logger = logging.getLogger("app.ai.rag")

NO_REPORTS = "No patient reports have been uploaded yet."


def _index_lines(lines: list[str], filename: str, user_id: int, document_id: int = None) -> int:
    """Embed `lines` into the user's pgvector table. Returns number of chunks."""
    embeddings = get_embeddings()
    if embeddings is None:
        logger.warning("embeddings unavailable; skipping indexing for user %s", user_id)
        return 0

    clean = [ln.strip() for ln in lines if ln and ln.strip()]
    if not clean:
        return 0

    documents = [
        Document(page_content=line, metadata={"source_file": filename, "user_id": user_id})
        for line in clean
    ]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(documents)

    if not chunks:
        return 0

    # Generate embeddings
    texts = [chunk.page_content for chunk in chunks]
    vectors = embeddings.embed_documents(texts)

    # Save to pgvector
    db = SessionLocal()
    try:
        db_chunks = []
        for chunk, vector in zip(chunks, vectors):
            db_chunks.append(
                DocumentChunk(
                    user_id=user_id,
                    document_id=document_id,
                    source_file=filename,
                    text=chunk.page_content,
                    embedding=vector
                )
            )
        db.add_all(db_chunks)
        db.commit()
    except Exception:
        logger.exception("Failed to insert pgvector chunks for user %s", user_id)
        db.rollback()
        return 0
    finally:
        db.close()

    return len(chunks)


def index_document_text(text: str, filename: str, user_id: int, document_id: int = None) -> int:
    """Index already-extracted text (e.g. OCR output from a report photo)."""
    return _index_lines((text or "").split("\n"), filename, user_id, document_id)


def process_and_index_document(content: bytes, filename: str, user_id: int, document_id: int = None) -> int:
    """Extract text from PDF bytes and index chunks into pgvector."""
    if get_embeddings() is None:
        logger.warning("embeddings unavailable; skipping indexing for user %s", user_id)
        return 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cleaned_lines = extract_text_from_pdf(tmp_path)
        return _index_lines(cleaned_lines, filename, user_id, document_id)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def retrieve_context(query: str, user_id: int, k: int = 3) -> str:
    """Search the user's pgvector chunks for relevant context."""
    embeddings = get_embeddings()
    if embeddings is None:
        return NO_REPORTS

    query_vector = embeddings.embed_query(query)
    
    db = SessionLocal()
    try:
        # Use pgvector's <=> (cosine distance) operator
        # Must cast array to vector literal
        vector_str = f"[{','.join(str(f) for f in query_vector)}]"
        stmt = text(
            "SELECT text, source_file FROM document_chunks "
            "WHERE user_id = :user_id "
            "ORDER BY embedding <=> :vector_str::vector "
            "LIMIT :k"
        )
        result = db.execute(stmt, {"user_id": user_id, "vector_str": vector_str, "k": k}).fetchall()
    except Exception:
        logger.exception("pgvector search failed for user %s", user_id)
        return NO_REPORTS
    finally:
        db.close()

    if not result:
        return "No relevant information found in your reports."

    return "\n\n".join(
        f"Excerpt from {row.source_file or 'unknown'}:\n{row.text}" for row in result
    )


def get_all_documents(user_id: int) -> str:
    """Return ALL indexed text content for a user."""
    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.user_id == user_id).all()
    except Exception:
        logger.exception("Failed to load chunks for user %s", user_id)
        return NO_REPORTS
    finally:
        db.close()

    if not chunks:
        return NO_REPORTS

    return "\n".join(chunk.text for chunk in chunks)


def delete_user_index(user_id: int) -> None:
    """Remove a user's entire vector index (used on account/data deletion)."""
    db = SessionLocal()
    try:
        db.execute(delete(DocumentChunk).where(DocumentChunk.user_id == user_id))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete user %s index", user_id)
    finally:
        db.close()
