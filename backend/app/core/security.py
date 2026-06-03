import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import jwt

from app.core.config import settings


import urllib.request
import json
from jose import jwt, jwk
from fastapi import HTTPException, status
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

# Cache the JWKS to avoid fetching on every request
_jwks = None
_jwks_fetched_at = 0.0
_JWKS_TTL = 3600  # Refresh JWKS every hour

def get_jwks(force_refresh: bool = False):
    import time
    global _jwks, _jwks_fetched_at
    now = time.time()
    if _jwks and not force_refresh and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks
    jwks_url = settings.CLERK_JWKS_URL
    if not jwks_url:
        raise ValueError("CLERK_JWKS_URL is not configured. Set it in backend/.env")
    
    logger.info(f"Fetching JWKS from {jwks_url}")
    with urllib.request.urlopen(jwks_url) as response:
        _jwks = json.loads(response.read().decode("utf-8"))
    _jwks_fetched_at = now
    logger.info(f"JWKS loaded with {len(_jwks.get('keys', []))} keys")
    return _jwks

def decode_access_token(token: str) -> dict:
    """Decode + verify a Clerk JWT using JWKS."""
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = _find_rsa_key(jwks, unverified_header.get("kid"))
        
        # If no matching key found, Clerk may have rotated keys — refresh and retry once
        if not rsa_key:
            logger.warning("No matching key for kid=%s in cached JWKS, refreshing...", unverified_header.get("kid"))
            jwks = get_jwks(force_refresh=True)
            rsa_key = _find_rsa_key(jwks, unverified_header.get("kid"))
        
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            return payload
        logger.error(f"No matching key found for kid={unverified_header.get('kid')} even after refresh")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate key.",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")


def _find_rsa_key(jwks: dict, kid: str) -> dict:
    """Find a matching RSA key in the JWKS by key ID."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    return {}


# ---------------------------------------------------------------------------
# Password utilities — still used by crud_user for legacy/local accounts
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

