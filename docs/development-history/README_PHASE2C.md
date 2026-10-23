# DoppleJa V1 — Phase 2C: Employer Profiles

A registered employer can be **a private person** (`private`) or **a business/organization** (`business`). This is not a company-only registration flow.

## Safe design
- Creates one new table, `employer_profiles`, linked to `users.id` (one profile per employer account).
- The existing `companies` table is **preserved**, not modified or deleted. We can retire it in a later reviewed migration if it has no records to migrate.
- The database enforces valid employer types. The API enforces verified login and the employer role.
- No CVs, applications, invoices, or legal-company-registration requirements.

## Installation
From `~/Desktop/DoppleJa_V1` on clean `develop` with Phase 2B committed and migrated:

```bash
unzip -o ~/Downloads/DoppleJa_Phase2C_EmployerProfiles_V1.zip -d .
docker compose exec api python -m alembic -c alembic.ini current
```

Before upgrading, the current revision should be `c84d20e5b319`. Inspect `backend/alembic/versions/f81c6e2a074b_create_employer_profiles.py`: the `upgrade()` function only creates the `employer_profiles` table. Then run:

```bash
docker compose exec api python -m alembic -c alembic.ini heads
docker compose exec api python -m alembic -c alembic.ini upgrade head
docker compose exec api python -m alembic -c alembic.ini current
docker compose exec api python -m pytest tests/ -v --tb=short
```

If model files are not reflected in the running API, use `docker compose up -d --build api`. The existing development bind mount usually makes rebuild unnecessary.

## Swagger
Log in as a verified employer at http://127.0.0.1:8001/docs and use `PUT /api/employers/me`.

Private employer example:
```json
{"employer_type":"private","display_name":"Max Müller","city":"Berlin","category":"Malerarbeiten","description":"Suche für zwei Tage Hilfe beim Streichen"}
```

Business employer example:
```json
{"employer_type":"business","display_name":"Nord Café","category":"Restaurant & Café","city":"Düsseldorf","description":"Kleines Café sucht Unterstützung"}
```

Retrieve with `GET /api/employers/me`. Expected 200 after save, 404 before first save, 401 when logged out, 403 for a worker account.

## Git
```bash
git diff --check
git add backend/app/main.py backend/app/models/__init__.py backend/app/models/employer.py backend/app/modules/employers backend/alembic/versions/f81c6e2a074b_create_employer_profiles.py tests/test_employers.py
git commit -m "feat: support private and business employer profiles"
git push origin develop
```

CI needs a migrated PostgreSQL/PostGIS test database. Do not run database integration tests against production. Existing test suite may still use your local development database and remove its own temporary users.
