#!/bin/sh
set -eu
log(){ printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"; }
require_env(){ eval "v=\${$1:-}"; [ -n "$v" ] || { log "ERROR missing environment variable: $1"; exit 1; }; }
wait_for_tcp(){ host="$1"; port="$2"; label="$3"; retries="${4:-30}"; i=1; while ! nc -z "$host" "$port" >/dev/null 2>&1; do [ "$i" -lt "$retries" ] || { log "ERROR $label unavailable"; exit 1; }; log "Waiting for $label at $host:$port ($i/$retries)"; i=$((i+1)); sleep 2; done; }
require_env DATABASE_URL
require_env JWT_SECRET_KEY
wait_for_tcp "${DATABASE_HOST:-postgres}" "${DATABASE_PORT:-5432}" PostgreSQL
if [ "${REDIS_REQUIRED:-true}" = true ]; then wait_for_tcp "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" Redis; fi
if [ "${VALIDATE_MODEL_ARTIFACTS:-true}" = true ]; then
  require_env FRAUD_MODEL_PATH
  [ -f "$FRAUD_MODEL_PATH" ] || { log "ERROR fraud model artifact unavailable: $FRAUD_MODEL_PATH"; exit 1; }
fi
if [ -d /app/.matplotlib-cache ]; then
  mkdir -p "${MPLCONFIGDIR:-/tmp/matplotlib}"
  cp -R /app/.matplotlib-cache/. "${MPLCONFIGDIR:-/tmp/matplotlib}/"
fi
if [ "${RUN_MIGRATIONS:-false}" = true ] && command -v alembic >/dev/null 2>&1 && [ -f /app/alembic.ini ]; then alembic upgrade head; fi
exec gunicorn --worker-class uvicorn.workers.UvicornWorker --workers "${WEB_CONCURRENCY:-4}" --bind "0.0.0.0:${PORT:-8000}" --timeout "${GUNICORN_TIMEOUT:-120}" --graceful-timeout 30 --keep-alive 5 --access-logfile - --error-logfile - --capture-output backend.app.main:app
