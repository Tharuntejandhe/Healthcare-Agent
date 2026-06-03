import uuid


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_signup_login_me_flow(client):
    email, password = _email(), "supersecret123"

    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": "Jane"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email

    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert r.json()["token_type"] == "bearer"

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_duplicate_signup_rejected(client):
    email, password = _email(), "supersecret123"
    assert client.post("/api/v1/auth/signup", json={"email": email, "password": password}).status_code == 200
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 400


def test_login_wrong_password(client):
    email, password = _email(), "supersecret123"
    client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", data={"username": email, "password": "wrongpass1"})
    assert r.status_code == 400


def test_short_password_rejected(client):
    r = client.post("/api/v1/auth/signup", json={"email": _email(), "password": "short"})
    assert r.status_code == 422  # pydantic min_length validation


def test_unauthenticated_returns_401_envelope(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    # Central error handler wraps everything in {"error": {...}}.
    body = r.json()
    assert "error" in body and "code" in body["error"] and "request_id" in body["error"]
