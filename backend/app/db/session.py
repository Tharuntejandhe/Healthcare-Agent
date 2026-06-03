from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Engine configuration supporting both PostgreSQL (production) and SQLite (dev).
if settings.is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 15}
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
else:
    # Postgres (Neon/managed): size the pool and recycle connections so we don't
    # hold stale ones across the provider's idle timeout.
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
        connect_args={"connect_timeout": 10},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
