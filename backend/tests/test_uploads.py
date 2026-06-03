def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_requires_auth(client):
    r = client.post("/api/v1/documents/upload", files={"file": ("x.pdf", b"%PDF-1.4 x", "application/pdf")})
    assert r.status_code == 401


def test_upload_rejects_non_pdf(client, auth_token):
    r = client.post(
        "/api/v1/documents/upload",
        headers=_auth(auth_token),
        files={"file": ("notes.txt", b"this is not a pdf", "text/plain")},
    )
    assert r.status_code == 400


def test_vision_rejects_non_image(client, auth_token):
    r = client.post(
        "/api/v1/vision/analyze-injury",
        headers=_auth(auth_token),
        files={"file": ("notes.txt", b"this is not an image", "text/plain")},
    )
    assert r.status_code == 400


def test_speech_rejects_non_audio(client, auth_token):
    r = client.post(
        "/api/v1/speech/transcribe",
        headers=_auth(auth_token),
        files={"file": ("notes.txt", b"this is not audio", "text/plain")},
    )
    assert r.status_code == 400


def test_speech_rejects_empty(client, auth_token):
    r = client.post(
        "/api/v1/speech/transcribe",
        headers=_auth(auth_token),
        files={"file": ("empty.webm", b"", "audio/webm")},
    )
    assert r.status_code == 400
