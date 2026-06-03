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
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise _CREDENTIALS_ERROR

    if token_data.sub is None:
        raise _CREDENTIALS_ERROR

    # Individually revoked (logout) — checked first; cheap primary-key lookup.
    if token_data.jti and crud.crud_token.is_revoked(db, jti=token_data.jti):
        raise _CREDENTIALS_ERROR

    user = crud.crud_user.get(db, id=int(token_data.sub))
    if not user:
        # A validly-signed token for a user that no longer exists is an auth
        # failure, not a 404 (which would leak account existence).
        raise _CREDENTIALS_ERROR

    # Globally invalidated (password change / logout-everywhere / compromise).
    if (token_data.ver or 0) != (user.token_version or 0):
        raise _CREDENTIALS_ERROR

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

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
