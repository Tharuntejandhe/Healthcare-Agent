import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.limits import limiter, rate_limit_handler
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = logging.getLogger("app.startup")
    log.info("starting %s in %s mode", settings.PROJECT_NAME, settings.ENVIRONMENT)

    # Ensure storage directories exist (local backend / FAISS / model cache).
    for path in (settings.uploads_path, settings.faiss_path):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            log.exception("could not create data directory %s", path)

    # In production, Alembic is the source of truth — never auto-create tables
    # (it can mask migration drift). Keep create_all only as a dev convenience.
    if not settings.is_production:
        try:
            Base.metadata.create_all(bind=engine)
            log.info("database tables verified (dev create_all)")
        except Exception:
            log.exception("database error during startup")

    yield
    log.info("shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Rate limiting (slowapi) — limiter lives on app.state; 429s use our error shape.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Centralized exception handlers.
register_exception_handlers(app)

# Middleware: applied in reverse order (last added runs first). CORS outermost so
# it always sees errors + OPTIONS, then security headers, then request-context.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Dev convenience: accept any localhost/127.0.0.1 port so the app keeps
    # working even when Next.js falls back to :3001/:3002/... In production we
    # rely solely on the explicit BACKEND_CORS_ORIGINS allowlist.
    allow_origin_regex=None if settings.is_production else r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.get("/")
def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API",
        "status": "online",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/livez")
def livez():
    """Liveness: the process is up. Cheap, never touches the DB."""
    return {"status": "alive"}


def _readiness(db: Session) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse({"status": "healthy", "database": "connected"})
    except Exception:
        logging.getLogger("app.health").exception("readiness check failed")
        # Return 503 so orchestrators/load balancers route away from this instance.
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "unavailable"})


@app.get("/readyz")
def readyz(db: Session = Depends(deps.get_db)):
    return _readiness(db)


@app.get("/health")
def health_check(db: Session = Depends(deps.get_db)):
    # Back-compat alias for /readyz.
    return _readiness(db)


app.include_router(api_router, prefix=settings.API_V1_STR)
