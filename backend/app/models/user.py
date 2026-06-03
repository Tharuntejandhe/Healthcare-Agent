from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Nullable so Google-only accounts (no local password) are valid.
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Bumped to invalidate every outstanding JWT for this user at once
    # (password change, "log out everywhere", suspected compromise). The token
    # carries a `ver` claim that must equal this value.
    token_version = Column(Integer, default=0, nullable=False, server_default="0")

    # OAuth fields
    auth_provider = Column(String, default="local", nullable=False)  # "local" | "google"
    google_sub = Column(String, unique=True, index=True, nullable=True)
    picture = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
