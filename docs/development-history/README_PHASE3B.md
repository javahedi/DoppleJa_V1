# DoppleJa V1 — Phase 3B: isolated tests + swipe engine

This overlay targets the existing Phase 3A source with revision `a9f8b2c3d401`. No old tables or data are dropped. The new `swipes` table records a job–worker pair and the side taking the action. **Matches and chat are intentionally NOT included yet.**

## Install on Mac (develop branch)

1. Complete and commit Phase 3A, push, and confirm a clean `git status`.
2. From `~/Desktop/DoppleJa_V1`, extract `DoppleJa_Phase3B_Swipes.zip` into the current folder. Files `backend/app/main.py`, `backend/app/models/__init__.py`, `.github/workflows/ci.yml`, `tests/test_jobs.py` are intentionally updated; other models remain unchanged.
3. **Create the test DB once** (this is a new database inside your existing PostGIS container, NOT an extra Docker service):

```bash
docker compose exec db psql -U doppleja_v1 -d postgres -c 'CREATE DATABASE doppleja_v1_test OWNER doppleja_v1;'
```

If it already exists, ignore the `already exists` error. Do not delete/reset any existing database.

4. Migrate your normal dev DB for Swagger:

```bash
docker compose exec api python -m alembic -c alembic.ini current
docker compose exec api python -m alembic -c alembic.ini heads
# Inspect the new revision: upgrade creates only the swipes table.
docker compose exec api python -m alembic -c alembic.ini upgrade head
```

5. Migrate the separate test DB (override only POSTGRES_DB in this one command):

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m alembic -c alembic.ini upgrade head
```

6. Run integration tests **against the test DB only**:

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short
```

`tests/conftest.py` prevents running Pytest if `POSTGRES_DB` does not end in `_test`. The CI workflow uses its own disposable PostGIS database named `doppleja_v1_test`.

## Swagger usage

`http://127.0.0.1:8001/docs`: 1) Log in as employer, make sure a job exists; GET `/api/discovery/workers?job_id=<job uuid>`; POST `/api/swipes` with `{ "job_id":"...", "worker_id":"<worker uuid>", "action":"like" }`. 2) Log in as worker with a profile, GET `/api/discovery/jobs`, POST `/api/swipes` with `{ "job_id":"...", "action":"like" }`. A repeated identical swipe is idempotent; changing it returns 409. The same card disappears from that actor's discovery feed. A match is *not* created yet.

## Important notes

- `get_database_url()` reads the env on first import. Use `docker compose exec -e ...` as shown; do not change `.env` just to test.
- Only the DB name is isolated; same PostgreSQL container and credentials are reused for convenience.
- Do **not** run `docker compose down -v`. No changes to the original old DoppleJa Docker project.
- Tests are integration tests. Do not use real user data in the `_test` DB.
- This is a development backend; secure cookies + CSRF, SMTP, and rate limiting still require finishing before a public launch.

## Git

```bash
git status
git add backend/app/main.py backend/app/models/__init__.py backend/app/models/swipe.py backend/app/modules/swipes backend/alembic/versions/7c91d4e5a602_create_swipes.py tests/conftest.py tests/test_jobs.py tests/test_swipes.py .github/workflows/ci.yml
git diff --cached --check
git commit -m 'feat: isolate tests and implement two-sided swipes'
git push origin develop
```
