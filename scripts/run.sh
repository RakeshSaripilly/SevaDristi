#!/usr/bin/env bash
# SevaDristi Production Entrypoint Script
set -eo pipefail

echo "=================================================="
echo " Starting SevaDristi Production Application Suite"
echo " Environment: ${ENVIRONMENT:-production}"
echo " DEMO_MODE: ${DEMO_MODE:-false}"
echo "=================================================="

# Run database migrations if PostgreSQL is configured
if [[ "${DATABASE_URL}" == *"postgresql"* ]]; then
  echo "[1/3] Executing Alembic database migrations..."
  alembic upgrade head || {
    echo "[WARNING] Alembic migrations reported an issue or already up-to-date."
  }
else
  echo "[1/3] Skipping Alembic PostgreSQL migration (SQLite/embedded mode)."
fi

# Validate rules catalog integrity
echo "[2/3] Validating Government Scheme Rules catalog..."
python -m backend.scripts.validate_rules || {
  echo "[ERROR] Scheme rules catalog validation failed. Refusing to boot."
  exit 1
}

# Launch Gunicorn with Uvicorn workers
WORKERS=${WEB_CONCURRENCY:-4}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "[3/3] Launching Gunicorn with ${WORKERS} Uvicorn workers on ${HOST}:${PORT}..."
exec gunicorn backend.main:app \
  --workers "${WORKERS}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "${HOST}:${PORT}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance \
  --timeout 60 \
  --keep-alive 5
