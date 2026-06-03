"""Test fixtures. Configures a throwaway SQLite DB and disables rate limiting +
RAG so tests never touch external services. Env is set BEFORE the app imports."""
import os
import pathlib

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("ENABLE_RAG", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("GROQ_API_KEY", "test-key")

# Keep uploads/FAISS out of the real data dir during tests.
_TEST_DATA = pathlib.Path(__file__).parent / "_test_data"
os.environ.setdefault("DATA_DIR", str(_TEST_DATA))

_TEST_DB = pathlib.Path(__file__).parent / "_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    # Fresh DB each session.
    if _TEST_DB.exists():
        _TEST_DB.unlink()
    from app.main import app  # imported here so env above is already set

    with TestClient(app) as c:  # entering the context runs the lifespan (create_all)
        yield c

    if _TEST_DB.exists():
        _TEST_DB.unlink()


@pytest.fixture
def auth_token(client):
    """Sign up a unique user and return a bearer token."""
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "supersecret123"
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": "Test User"})
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]
