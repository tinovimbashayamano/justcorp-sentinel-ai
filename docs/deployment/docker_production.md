# JustCorp Sentinel AI — Production Docker Deployment

This package provides multi-stage backend and frontend images, Nginx reverse proxying, PostgreSQL and Redis, non-root application containers, health checks, persistent volumes, network isolation, log rotation, resource limits, environment templates, and a lazy-loading example.

## Assumptions

- FastAPI import: `backend.app.main:app`
- Backend health endpoint: `GET /health`
- Frontend build command: `npm run build`
- Frontend output: `frontend/dist`
- Production API base URL: `/` (API modules already include `/api/v1`)
- PostgreSQL driver: `psycopg2`
- Model artifact: `/app/ml/model_artifacts/lightgbm_fraud_model.joblib`
- Report storage: `/app/storage/reports`
- Evidence storage: `/app/storage/evidence`
- Gunicorn and library runtime caches: `/tmp`

Adjust these when your repository differs.

## Setup

```powershell
Copy-Item .env.production.example .env.production
notepad .env.production
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use different generated values for PostgreSQL, Redis, and JWT secrets. Never commit `.env.production`.
The PostgreSQL password must be replaced both in `POSTGRES_PASSWORD` and in
the password section of `DATABASE_URL`.

## Validate

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

The deployment helper rejects files containing `REPLACE_WITH_`, `CHANGE_ME`,
or `CHANGEME`:

```powershell
.\scripts\production.ps1 validate
```

## Build and run

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml build --pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Open `http://localhost:8080`.

Docker Desktop must be running before `build` or `up`.

## Logs

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f
```

## Persistence

Restart services and confirm database records, Redis state, generated reports, and model artifacts remain. Do not use `down -v` unless intentionally deleting data.

## Lazy loading

The real router in `frontend/src/App.jsx` now uses `lazy` and `Suspense` for
workspace pages. `frontend/src/routes/lazyRoutes.example.jsx` remains a compact
reference and must not be mounted as a second `Routes` tree.

## HTTPS

Terminate TLS in front of this container stack. Add HSTS only after HTTPS is active.

## Security checks

- Ensure `.env.production` is ignored.
- Confirm secrets are absent from images.
- Keep PostgreSQL and Redis private.
- Configure explicit CORS origins and trusted hosts.
- Replace `FRONTEND_ORIGIN` and `TRUSTED_HOSTS` with the production hostname.
- Configure backups and test restoration.
- Scan dependencies and container images.

The backend filesystem is read-only. `HOME` and Gunicorn's worker temporary
directory point to the container's writable `/tmp` mount. Matplotlib's font
cache is generated once while the backend image is built, then copied from
`/app/.matplotlib-cache` to writable `/tmp/matplotlib` before Gunicorn starts.
This prevents every worker from rebuilding it during startup while preserving
the read-only application filesystem. The Nginx entrypoint may report that it
cannot rewrite `default.conf`; this is expected because the production
configuration is intentionally read-only and Nginx continues normally.

The verification script checks the owner of `/proc/1` inside each running
container. This avoids a false failure for PostgreSQL, whose official
entrypoint can begin as root to prepare the data volume before replacing
itself with the non-root PostgreSQL server process. Redis uses a direct
`redis-server` command so its official entrypoint can prepare `/data` before
dropping privileges to the built-in `redis` user.
