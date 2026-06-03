#!/usr/bin/env sh
# Container entrypoint: apply DB migrations, then start the app.
# Runs once per container (before gunicorn forks workers), so migrations are
# applied on every deploy/restart and are idempotent if already up to date.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[start] applying database migrations (alembic upgrade head)..."
  alembic upgrade head
fi

echo "[start] launching gunicorn on 0.0.0.0:${PORT:-8000} with ${WEB_CONCURRENCY:-2} worker(s)..."
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w "${WEB_CONCURRENCY:-2}" \
  -b "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile -
