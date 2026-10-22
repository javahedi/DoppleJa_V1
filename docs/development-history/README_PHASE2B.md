# DoppleJa V1 — Phase 2B Worker Profiles

This overlay adds a small worker-profile API. It assumes Phase 2A is already applied and committed.

## Before installing

Commit and push Phase 2A to `develop` first; wait for CI to pass. Do not paste any secret values into GitHub.

## Install

From `~/Desktop/DoppleJa_V1` on `develop`, with a clean working tree:

```bash
unzip -o ~/Downloads/DoppleJa_Phase2B_overlay.zip -d .
docker compose exec api python -m alembic -c alembic.ini heads
```

Confirm the head is `c84d20e5b319`. Then apply the migration:

```bash
docker compose exec api python -m alembic -c alembic.ini upgrade head
docker compose exec api python -m alembic -c alembic.ini current
```

Because your Compose setup mounts `backend/` and `tests/`, normally there is no rebuild required. If tests are not mounted, add `./tests:/code/tests:ro` to the API volumes (Phase 2A setup).

Run tests:

```bash
docker compose exec api python -m pytest tests/ -v --tb=short
```

Swagger: `http://127.0.0.1:8001/docs`.

## New endpoints

`GET /api/workers/me` — returns profile or 404 when not set.

`PUT /api/workers/me` — create or replace profile for logged-in verified worker; requires `display_name`. `profession`, `city`, `availability`, `bio`, and `photo_url` are optional.

Both require a valid login cookie. Employer accounts get HTTP 403.

A photo URL is only a placeholder for future image-upload functionality; no file-upload infrastructure yet. Do not submit sensitive information in biography.

## Commit only after tests pass

```bash
git add backend/app/main.py backend/app/models/worker.py backend/app/modules/workers backend/alembic/versions/c84d20e5b319_add_worker_profession.py tests/test_workers.py
git commit -m "feat: add worker profile API"
git push origin develop
```

## Safety

The existing tests create temporary accounts in the configured database and delete them after testing. Prefer a separate test database, particularly before real accounts are stored. We will not run tests against production.
