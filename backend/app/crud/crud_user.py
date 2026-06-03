from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


def get_by_email(db: Session, *, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_by_google_sub(db: Session, *, google_sub: str) -> Optional[User]:
    return db.query(User).filter(User.google_sub == google_sub).first()


def get(db: Session, id: int) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def create(db: Session, *, obj_in: UserCreate) -> User:
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
        is_superuser=obj_in.is_superuser,
        is_active=obj_in.is_active,
        auth_provider="local",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_google_user(
    db: Session,
    *,
    email: str,
    full_name: Optional[str],
    google_sub: str,
    picture: Optional[str] = None,
) -> User:
    db_obj = User(
        email=email,
        hashed_password=None,
        full_name=full_name,
        is_active=True,
        is_superuser=False,
        auth_provider="google",
        google_sub=google_sub,
        picture=picture,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def link_google_account(
    db: Session,
    *,
    user: User,
    google_sub: str,
    picture: Optional[str] = None,
) -> User:
    """Attach a Google identity to an existing local account."""
    user.google_sub = google_sub
    if picture and not user.picture:
        user.picture = picture
    # We keep auth_provider as-is ("local") so the user can still sign in
    # with their password; google_sub being set is what enables Google login.
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def bump_token_version(db: Session, *, user: User) -> User:
    """Invalidate every outstanding JWT for this user ("log out everywhere")."""
    user.token_version = (user.token_version or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, *, user: User, new_password: str) -> User:
    """Change the password and invalidate all existing sessions."""
    user.hashed_password = get_password_hash(new_password)
    user.token_version = (user.token_version or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, *, user: User) -> None:
    db.delete(user)
    db.commit()
