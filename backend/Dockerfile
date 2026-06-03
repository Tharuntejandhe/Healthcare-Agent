# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # gunicorn defaults (overridable at runtime)
    WEB_CONCURRENCY=2 \
    PORT=8000 \
    DATA_DIR=/app/data

WORKDIR /app

# Build deps for psycopg2 etc. (kept minimal; slim image).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

# Run as a non-root user; own /app (incl. the default DATA_DIR) so uploads,
# FAISS indexes and the embedding-model cache are writable.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p "$DATA_DIR" \
    && chmod +x /app/start.sh \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container-level healthcheck hits the cheap liveness probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/livez" || exit 1

# Entrypoint applies migrations then launches gunicorn (uvicorn workers).
CMD ["/app/start.sh"]
