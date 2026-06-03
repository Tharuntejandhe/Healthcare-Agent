import logging
from typing import Generator, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload

logger = logging.getLogger("app.api.deps")

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def _resolve_user(db: Session, token: str) -> Tuple[User, TokenPayload]:
    try:
        payload = security.decode_access_token(token)
        # Clerk JWT uses 'sub' for the user ID
        sub = payload.get("sub")
        if not sub:
            logger.error("JWT decoded but 'sub' claim is missing. Payload keys: %s", list(payload.keys()))
            raise _CREDENTIALS_ERROR
    except _CREDENTIALS_ERROR.__class__:
        raise
    except Exception as e:
        logger.error("JWT verification failed: %s: %s", type(e).__name__, e)
        raise _CREDENTIALS_ERROR

    # Look up user by clerk_id (stored in google_sub column)
    user = crud.crud_user.get_by_google_sub(db, google_sub=sub)
    if not user:
        # Auto-provision user on first valid Clerk token
        user = crud.crud_user.create_google_user(
            db=db,
            email=f"{sub}@clerk.local",
            full_name="Patient",
            google_sub=sub,
        )
        user.auth_provider = "clerk"
        db.commit()

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Create dummy token payload since we don't need jti/ver anymore
    token_data = TokenPayload(sub=str(user.id))
    return user, token_data


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    user, _ = _resolve_user(db, token)
    return user


def get_current_user_with_claims(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> Tuple[User, TokenPayload]:
    """Like get_current_user but also returns the token claims (for logout)."""
    return _resolve_user(db, token)
