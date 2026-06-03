"""Tests for token revocation, logout, logout-all and password change."""
import uuid


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def _signup_login(client):
    email, password = _email(), "supersecret123"
    client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return email, password, r.json()["access_token"]


def test_logout_revokes_token(client):
    _, _, token = _signup_login(client)
    h = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=h).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=h).status_code == 200
    # The same token must now be rejected (server-side denylist).
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_logout_all_invalidates_existing_token(client):
    _, _, token = _signup_login(client)
    h = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/v1/auth/logout-all", headers=h).status_code == 200
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_password_change_invalidates_old_token_and_issues_new(client):
    email, password, token = _signup_login(client)
    h = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/users/me/password",
        headers=h,
        json={"current_password": password, "new_password": "brandnewpass123"},
    )
    assert r.status_code == 200, r.text
    new_token = r.json()["access_token"]

    # Old token is now stale (token_version bumped); new token works.
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    assert client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"}
    ).status_code == 200

    # Old password no longer works; new one does.
    assert client.post("/api/v1/auth/login", data={"username": email, "password": password}).status_code == 400
    assert client.post("/api/v1/auth/login", data={"username": email, "password": "brandnewpass123"}).status_code == 200


def test_password_change_wrong_current_rejected(client):
    _, _, token = _signup_login(client)
    r = client.post(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrongpassword", "new_password": "brandnewpass123"},
    )
    assert r.status_code == 400
