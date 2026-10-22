# DoppleJa Phase 2A overlay

This archive is an overlay of **new and updated** files, not a full application. Extract into the existing `~/Desktop/DoppleJa_V1` root on the `develop` branch. Existing `worker.py`, `company.py`, `core/database.py`, and Alembic history remain untouched.

## Requirements and Docker environment

Add these dependencies to the **existing** `backend/requirements.txt` (do not replace it):

```
argon2-cffi>=23,<27
PyJWT>=2.9,<3
email-validator>=2,<3
```

Generate a local secret once: `python -c 'import secrets; print(secrets.token_urlsafe(48))'`. Add to your existing `.env` (do not commit):

```
AUTH_SECRET_KEY=<your-generated-secret>
AUTH_COOKIE_SECURE=false
AUTH_DEV_PRINT_LINK=true
PUBLIC_API_URL=http://127.0.0.1:8001
```

Add to the `api` service `environment:` section in `compose.yaml`:

```yaml
      AUTH_SECRET_KEY: ${AUTH_SECRET_KEY:?required}
      AUTH_COOKIE_SECURE: ${AUTH_COOKIE_SECURE:-false}
      AUTH_DEV_PRINT_LINK: ${AUTH_DEV_PRINT_LINK:-false}
      PUBLIC_API_URL: ${PUBLIC_API_URL:-http://127.0.0.1:8001}
```

For development tests in Docker, add under the api service `volumes:` list:

```yaml
      - ./tests:/code/tests:ro
```

Then:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose exec api python -m alembic -c alembic.ini upgrade head
docker compose exec api python -m pytest tests/ -v
```

## Registration and verification

In `http://127.0.0.1:8001/docs`, use POST `/api/auth/register` with an email, 10+ character password and `worker`/`employer` role. Retrieve the one-time verification link using `docker compose logs --tail=60 api`; open it in browser. Then POST `/api/auth/login`, followed by GET `/api/auth/me` in the same browser session. The Swagger UI may not always send cookies from different origins; use the same host and port.

**Before production:** Set `AUTH_COOKIE_SECURE=true`, `AUTH_DEV_PRINT_LINK=false`, and configure `SMTP_HOST`, `SMTP_FROM`, `SMTP_PORT`, and optional `SMTP_USERNAME`, `SMTP_PASSWORD` inside the API environment. Use HTTPS and a real email domain. Add request rate limiting, resend verification, password reset, and CSRF protection for cookie-authenticated state-changing endpoints before public launch.

## GitHub Actions CI

The archive includes a complete replacement `.github/workflows/ci.yml` that adds a disposable PostgreSQL/PostGIS test service and applies Alembic migrations before testing. This replaces your existing CI workflow. For reference, its important service definition is:

```yaml
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_USER: doppleja_v1
          POSTGRES_PASSWORD: ci-password-only
          POSTGRES_DB: doppleja_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U doppleja_v1 -d doppleja_test"
          --health-interval 5s --health-timeout 5s --health-retries 10
```

For the test job, set env:

```
POSTGRES_USER: doppleja_v1
POSTGRES_PASSWORD: ci-password-only
POSTGRES_DB: doppleja_test
DB_HOST: localhost
AUTH_SECRET_KEY: a-ci-only-secret-not-used-in-production
AUTH_COOKIE_SECURE: 'false'
PUBLIC_API_URL: http://localhost:8001
```

Before pytest, run `python -m alembic -c alembic.ini upgrade head`. The migration will not touch extension tables (your existing include_name filter). Tests use unique temporary users and remove them after runs. For CI, no mail provider is required because the test monkeypatches email delivery.

## Notes

This initial phase keeps password_hash non-null and implements email/password only. Google and Apple can be added later through a dedicated `auth_identities` migration. Verification links printed to logs are **for local development only**. The generated verification token is stored only as SHA-256 hash. A committed user may remain unverified if SMTP delivery fails; add retry/resend before production.
