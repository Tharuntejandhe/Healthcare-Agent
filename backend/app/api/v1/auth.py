from datetime import datetime, timedelta, timezone
from typing import Any, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.limits import AUTH_LIMIT, limiter
from app.models.user import User
from app.schemas.token import Token, TokenPayload
from app.schemas.user import GoogleAuthRequest, UserCreate, UserResponse
from app.services.audit import record_event

router = APIRouter()


def _issue_token(user: User) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id,
            token_version=user.token_version or 0,
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_LIMIT)
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """OAuth2 password flow — issues a JWT for an existing local account."""
    user = crud.crud_user.get_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        record_event(
            db, action="auth.login", resource_type="auth", status="denied",
            request=request, detail=f"email={form_data.username}",
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    record_event(db, action="auth.login", resource_type="auth", user_id=user.id, request=request)
    return _issue_token(user)


@router.post("/signup", response_model=UserResponse)
@limiter.limit(AUTH_LIMIT)
def create_user_signup(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """Create a local-password account."""
    existing = crud.crud_user.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )
    user = crud.crud_user.create(db, obj_in=user_in)
    record_event(db, action="auth.signup", resource_type="auth", user_id=user.id, request=request)
    return user


@router.post("/google", response_model=Token)
@limiter.limit(AUTH_LIMIT)
def google_sign_in(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    payload: GoogleAuthRequest,
) -> Any:
    """Sign in (or sign up) with a Google ID token.

    Flow:
      1. Frontend uses Google Identity Services to obtain an ID token.
      2. POST { id_token } here.
      3. We verify the token, look up / create the user, and issue our JWT.
    """
    try:
        claims = security.verify_google_id_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    google_sub = claims.get("sub")
    email = claims.get("email")
    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token missing required claims.",
        )

    full_name = claims.get("name") or claims.get("given_name")
    picture = claims.get("picture")

    user = crud.crud_user.get_by_google_sub(db, google_sub=google_sub)
    if user is None:
        # No Google-linked account yet — see if the verified email matches an existing local user.
        existing = crud.crud_user.get_by_email(db, email=email)
        if existing:
            user = crud.crud_user.link_google_account(
                db, user=existing, google_sub=google_sub, picture=picture
            )
        else:
            user = crud.crud_user.create_google_user(
                db,
                email=email,
                full_name=full_name,
                google_sub=google_sub,
                picture=picture,
            )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    record_event(db, action="auth.login.google", resource_type="auth", user_id=user.id, request=request)
    return _issue_token(user)


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: UserResponse = Depends(deps.get_current_user),
) -> Any:
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(deps.get_db),
    user_claims: Tuple[User, TokenPayload] = Depends(deps.get_current_user_with_claims),
) -> Any:
    """Revoke the current access token (single-session logout).

    Unlike a purely client-side logout, this adds the token's `jti` to a
    server-side denylist so a copy of the token (e.g. exfiltrated) is useless.
    """
    user, claims = user_claims
    if claims.jti and claims.exp:
        crud.crud_token.revoke(
            db,
            jti=claims.jti,
            expires_at=datetime.fromtimestamp(claims.exp, tz=timezone.utc),
            user_id=user.id,
        )
    record_event(db, action="auth.logout", resource_type="auth", user_id=user.id, request=request)
    return {"message": "Logged out."}


@router.post("/logout-all")
def logout_all(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Invalidate every active session for this user (e.g. after a device loss)."""
    crud.crud_user.bump_token_version(db, user=current_user)
    record_event(db, action="auth.logout_all", resource_type="auth", user_id=current_user.id, request=request)
    return {"message": "All sessions have been signed out."}
