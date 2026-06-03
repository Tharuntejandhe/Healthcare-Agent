import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import jwt

from app.core.config import settings


def create_access_token(
    subject: Union[str, Any],
    *,
    token_version: int = 0,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Mint a signed JWT.

    Includes a unique `jti` (so the token can be revoked individually on logout)
    and a `ver` claim mirroring the user's `token_version` (so every token for a
    user can be invalidated at once by bumping that counter).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "jti": uuid.uuid4().hex,
        "ver": token_version,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode + verify a JWT, pinning the expected algorithm.

    Passing an explicit single-element `algorithms` list ensures python-jose
    rejects `alg: none` and RS256→HS256 algorithm-confusion forgery attempts.
    Raises jose.JWTError on any invalid/expired/tampered token.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    if not hashed_password:
        # Accounts created via Google have no password hash.
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google ID token and return the decoded claims.

    Raises ValueError if the token is invalid, expired, or for the wrong client.
    `google-auth` is imported lazily so the dependency is only required when
    Google login is actually used.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured on the server.")

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:  # pragma: no cover - install-time only
        raise RuntimeError(
            "google-auth is not installed. Add `google-auth>=2.28.0` to requirements.txt."
        ) from exc

    try:
        claims = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise ValueError(f"Invalid Google ID token: {exc}") from exc

    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Google ID token has an unexpected issuer.")
    if not claims.get("email_verified"):
        raise ValueError("Google account email is not verified.")
    return claims
