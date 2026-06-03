"""Tests for document metadata, listing, export, account deletion, audit log."""
import uuid

# Minimal valid PDF (magic bytes + trivial structure) accepted by ensure_pdf.
_PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _auth(client):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "supersecret123"
    client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_upload_then_list_then_delete(client):
    _, h = _auth(client)

    # Empty to start.
    r = client.get("/api/v1/documents", headers=h)
    assert r.status_code == 200
    assert r.json()["documents"] == []

    # Upload (RAG disabled in tests → chunks_indexed 0, but metadata persists).
    r = client.post(
        "/api/v1/documents/upload",
        headers=h,
        files={"file": ("labs.pdf", _PDF_BYTES, "application/pdf")},
    )
    assert r.status_code == 200, r.text
    blob = r.json()["blob_name"]
    assert r.json()["filename"] == "labs.pdf"

    # Now listed from the DB (not localStorage).
    r = client.get("/api/v1/documents", headers=h)
    docs = r.json()["documents"]
    assert len(docs) == 1 and docs[0]["blob_name"] == blob

    # Delete removes the row.
    assert client.request("DELETE", f"/api/v1/documents/{blob}", headers=h).status_code == 200
    assert client.get("/api/v1/documents", headers=h).json()["documents"] == []


def test_other_user_cannot_read_my_file(client):
    _, h1 = _auth(client)
    r = client.post(
        "/api/v1/documents/upload",
        headers=h1,
        files={"file": ("labs.pdf", _PDF_BYTES, "application/pdf")},
    )
    blob = r.json()["blob_name"]  # "user_<id>/<uuid>.pdf"

    _, h2 = _auth(client)
    # user 2 tries to fetch user 1's file via the local serving route
    r = client.get(f"/api/v1/documents/local/{blob}", headers=h2)
    assert r.status_code == 403


def test_export_contains_profile_and_documents(client):
    email, h = _auth(client)
    client.post(
        "/api/v1/documents/upload",
        headers=h,
        files={"file": ("labs.pdf", _PDF_BYTES, "application/pdf")},
    )
    r = client.get("/api/v1/users/me/export", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["profile"]["email"] == email
    assert len(body["documents"]) == 1


def test_activity_log_records_events(client):
    _, h = _auth(client)
    client.get("/api/v1/documents", headers=h)
    r = client.get("/api/v1/users/me/activity", headers=h)
    assert r.status_code == 200
    actions = {e["action"] for e in r.json()["events"]}
    # signup + login were audited at minimum.
    assert "auth.login" in actions


def test_account_deletion_purges_and_invalidates(client):
    _, h = _auth(client)
    client.post(
        "/api/v1/documents/upload",
        headers=h,
        files={"file": ("labs.pdf", _PDF_BYTES, "application/pdf")},
    )
    assert client.request("DELETE", "/api/v1/users/me", headers=h).status_code == 200
    # Token for a now-deleted user must be rejected.
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
