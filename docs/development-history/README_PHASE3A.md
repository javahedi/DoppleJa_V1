# DoppleJa V1 — Phase 3A: Job cards & categories

## Scope
One simple job card per open role or short gig, posted by a verified employer (private OR business). No CVs, applications, matching, payments or chat in this phase. Existing database tables are preserved.

## First: finish Phase 2C
Confirm the `develop` branch is clean and Phase 2C is committed and pushed. The current Alembic revision must be `f81c6e2a074b` before applying Phase 3A.

## Install
From `~/Desktop/DoppleJa_V1`:

```bash
unzip -o ~/Downloads/DoppleJa_Phase3A_Jobs.zip -d .
docker compose exec api python -m alembic -c alembic.ini heads
# Inspect the new migration: it must ONLY create job_categories and jobs.
docker compose exec api python -m alembic -c alembic.ini upgrade head
docker compose exec api python -m alembic -c alembic.ini current
docker compose exec api python -m pytest tests/ -v --tb=short
```

New revision: `a9f8b2c3d401`. It creates `job_categories` with 9 fixed categories and `jobs`, with FK to employer_profiles. `companies` remains untouched.

If Swagger does not show Jobs, run `docker compose restart api`; the backend folder is bind-mounted with reload enabled.

## Swagger
1. Sign in using a verified employer with an existing profile (e.g. Nord Café).
2. GET `/api/categories` to see the IDs.
3. POST `/api/jobs`:

```json
{"category_id":1,"title":"Servicekraft (m/w/d)","description":"Flexible Schichten, freundliches Team.","city":"Düsseldorf","work_type":"part_time","hourly_pay_min":15,"hourly_pay_max":18,"is_active":true}
```

4. GET `/api/jobs/mine` to review your postings. PUT `/api/jobs/{job_id}` to edit or deactivate.
5. Log in as a verified worker. GET `/api/jobs/discover?city=Düsseldorf` to see active jobs. GET `/api/jobs/{job_id}` to see job detail.

Other accepted work types: `minijob`, `full_time`, `temporary`.
No PostGIS radius yet; Phase 3B will add locations and swipe interactions.

## Git
```bash
git add backend/app/main.py backend/app/models/__init__.py backend/app/models/job.py backend/app/modules/jobs backend/alembic/versions/a9f8b2c3d401_add_job_categories_and_jobs.py tests/test_jobs.py
git diff --cached --check
git commit -m "feat: add simple job cards and categories"
git push origin develop
```

## Safeguards
Do not run `docker compose down -v` and do not apply migration if the preceding Phase 2C revision is missing. Local integration tests currently use the dev DB and delete their own temporary records; isolate them before any live data is introduced.
