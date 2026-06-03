from pathlib import Path
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings

# Resolve paths relative to the backend root (backend/app/core/config.py -> backend/)
BACKEND_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    # --- App metadata ---
    PROJECT_NAME: str = "MediHealth System"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # --- Security ---
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY: str = "super-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # --- CORS ---
    # Comma-separated list, e.g. "http://localhost:3000,https://app.example.com"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///sql_app.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE_SECONDS: int = 1800

    # --- Storage ---
    # Where uploads + FAISS indexes live. On Render, point this at a mounted disk.
    DATA_DIR: str = str(BACKEND_ROOT / "data")
    # "local" (default, no cloud dependency) or "azure".
    STORAGE_BACKEND: Literal["local", "azure"] = "local"

    # --- Upload limits (MB) ---
    MAX_UPLOAD_MB: int = 15        # PDFs
    MAX_IMAGE_MB: int = 10         # injury photos
    MAX_AUDIO_MB: int = 25         # voice clips

    # --- AI / 3rd-party API keys ---
    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # --- AI models / behavior ---
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"
    GROQ_TIMEOUT_SECONDS: float = 60.0
    GROQ_MAX_RETRIES: int = 2

    # RAG / embeddings
    ENABLE_RAG: bool = True
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # --- Rate limiting (slowapi) ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_AI: str = "20/minute"
    # "memory://" (per-process) or a shared backend like "redis://host:6379"
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    # --- Azure Storage (only used when STORAGE_BACKEND=azure) ---
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_CONTAINER_NAME: str = "patient-reports"

    # --- Clerk Auth ---
    CLERK_JWKS_URL: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": str(ENV_FILE),
        "case_sensitive": True,
        "extra": "ignore",
    }

    # ----- Derived helpers -----
    @property
    def cors_origins(self) -> List[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def uploads_path(self) -> Path:
        return self.data_path / "uploads"

    @property
    def faiss_path(self) -> Path:
        return self.data_path / "faiss_index"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def max_image_bytes(self) -> int:
        return self.MAX_IMAGE_MB * 1024 * 1024

    @property
    def max_audio_bytes(self) -> int:
        return self.MAX_AUDIO_MB * 1024 * 1024

    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "super-secret-key-please-change-in-production" or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be a strong, unique value (>=32 chars) in production."
                )
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError(
                    "BACKEND_CORS_ORIGINS must not contain '*' in production; list explicit origins."
                )
            if self.is_sqlite:
                raise ValueError(
                    "SQLite is not supported in production (ephemeral disk + concurrency). "
                    "Set DATABASE_URL to a managed Postgres connection string."
                )
            if self.STORAGE_BACKEND == "azure" and not self.AZURE_STORAGE_CONNECTION_STRING:
                raise ValueError(
                    "STORAGE_BACKEND=azure requires AZURE_STORAGE_CONNECTION_STRING."
                )
        return self


settings = Settings()
