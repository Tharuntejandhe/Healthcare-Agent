"""User-isolated RAG over FAISS, using real local embeddings.

Security note: FAISS indexes are pickled, so loading requires
allow_dangerous_deserialization=True. We only ever load indexes we created
ourselves under settings.faiss_path/user_<id>/ (server-generated paths, never
client-controlled), so this is an internal trust boundary — do not point the
loader at untrusted directories.
"""
import logging
import os
import shutil
import tempfile
import threading

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.ai.embeddings import get_embeddings
from app.services.pdf_processor import extract_text_from_pdf

logger = logging.getLogger("app.ai.rag")

NO_REPORTS = "No patient reports have been uploaded yet."

# A FAISS index is NOT safe under concurrent index-changing operations and has
# no internal locking, so two simultaneous uploads for the same user could
# silently drop one report's chunks (lost update) or corrupt the on-disk pair.
# We serialize per-user writes with a lock. NOTE: this protects within a single
# process only; across multiple gunicorn workers/instances an external lock
# (Redis/advisory) or a single-writer design is still required — but Render's
# single-instance disk model means the only concurrency here today is threads.
_user_locks: dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def _user_lock(user_id: int) -> threading.Lock:
    with _locks_guard:
        lock = _user_locks.get(user_id)
        if lock is None:
            lock = threading.Lock()
            _user_locks[user_id] = lock
        return lock


def get_user_index_path(user_id: int) -> str:
    """Path to the FAISS index for a specific user."""
    return str(settings.faiss_path / f"user_{user_id}")


def _atomic_save(vector_store: "FAISS", user_index_path: str) -> None:
    """Save the index via a temp dir + rename so a crash can't leave a torn pair.

    FAISS.save_local writes index.faiss + index.pkl; writing them straight into
    the live directory risks a half-written/mismatched pair on crash. We write to
    a sibling temp dir on the same filesystem, then os.replace each file into
    place (atomic per file).
    """
    parent = os.path.dirname(user_index_path) or "."
    os.makedirs(parent, exist_ok=True)
    os.makedirs(user_index_path, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix=".faiss_tmp_", dir=parent)
    try:
        vector_store.save_local(tmp_dir)
        for name in os.listdir(tmp_dir):
            os.replace(os.path.join(tmp_dir, name), os.path.join(user_index_path, name))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def delete_user_index(user_id: int) -> None:
    """Remove a user's entire FAISS index (used on account/data deletion)."""
    with _user_lock(user_id):
        path = get_user_index_path(user_id)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)


def _index_lines(lines: list[str], filename: str, user_id: int) -> int:
    """Embed `lines` into the user's FAISS index (locked + atomic). Returns chunks.

    Shared core for both the PDF path and the image-OCR path. Returns 0 if
    embeddings are unavailable (RAG disabled / model failed) — upload still ok.
    """
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

    user_index_path = get_user_index_path(user_id)
    # Serialize per-user load->add->save so concurrent uploads can't drop chunks
    # or corrupt the index; persist atomically.
    with _user_lock(user_id):
        if os.path.exists(user_index_path):
            vector_store = FAISS.load_local(user_index_path, embeddings, allow_dangerous_deserialization=True)
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)
        _atomic_save(vector_store, user_index_path)
    return len(chunks)


def index_document_text(text: str, filename: str, user_id: int) -> int:
    """Index already-extracted text (e.g. OCR output from a report photo)."""
    return _index_lines((text or "").split("\n"), filename, user_id)


def process_and_index_document(content: bytes, filename: str, user_id: int) -> int:
    """Extract text from PDF bytes and (re)build the user's FAISS index.

    Synchronous and CPU/IO-bound — call it from a threadpool (the router runs in
    one). Returns the number of indexed chunks, or 0 if embeddings are
    unavailable (RAG disabled / model failed to load) — the upload still succeeds.
    """
    if get_embeddings() is None:
        logger.warning("embeddings unavailable; skipping indexing for user %s", user_id)
        return 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cleaned_lines = extract_text_from_pdf(tmp_path)
        return _index_lines(cleaned_lines, filename, user_id)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def retrieve_context(query: str, user_id: int, k: int = 3) -> str:
    """Search the user's FAISS index for relevant context."""
    embeddings = get_embeddings()
    if embeddings is None:
        return NO_REPORTS

    user_index_path = get_user_index_path(user_id)
    if not os.path.exists(user_index_path):
        return NO_REPORTS

    try:
        vector_store = FAISS.load_local(user_index_path, embeddings, allow_dangerous_deserialization=True)
        docs = vector_store.similarity_search(query, k=k)
    except Exception:
        logger.exception("FAISS search failed for user %s", user_id)
        return NO_REPORTS

    if not docs:
        return "No relevant information found in your reports."

    return "\n\n".join(
        f"Excerpt from {doc.metadata.get('source_file', 'unknown')}:\n{doc.page_content}" for doc in docs
    )


def get_all_documents(user_id: int) -> str:
    """Return ALL indexed text content for a user."""
    embeddings = get_embeddings()
    if embeddings is None:
        return NO_REPORTS

    user_index_path = get_user_index_path(user_id)
    if not os.path.exists(user_index_path):
        return NO_REPORTS

    try:
        vector_store = FAISS.load_local(user_index_path, embeddings, allow_dangerous_deserialization=True)
        all_docs = list(vector_store.docstore._dict.values())
    except Exception:
        logger.exception("FAISS load failed for user %s", user_id)
        return NO_REPORTS

    if not all_docs:
        return NO_REPORTS

    return "\n".join(doc.page_content for doc in all_docs)
