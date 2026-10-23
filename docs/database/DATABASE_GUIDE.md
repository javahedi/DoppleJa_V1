# DoppleJa V1 — Database Developer Guide

**Project:** [javahedi/DoppleJa_V1](https://github.com/javahedi/DoppleJa_V1)
**Audience:** DoppleJa collaborators
**Maintainer and final merge decision-maker:** Repository owner (`javahedi`)
**Updated:** 23 October 2026

> **Purpose:** Understand the current database architecture, create a separate local demo environment, inspect the schema, and collaborate safely. This guide documents the project's reported implementation and provides verification commands. **The actual repository models and Alembic migrations are the source of truth** for column types, foreign keys, constraints, and indexes.

## 1. Architecture overview

DoppleJa matches workers and employers via mutual Likes. Once both sides Like, a Match is created and direct chat becomes available. The backend uses **FastAPI + SQLAlchemy** to access **PostgreSQL 16 / PostGIS**, with **Alembic** managing schema migrations. Docker Compose runs the development services. Redis is also part of the application stack.

```text
Browser / HTML / CSS / JavaScript
            |
            v
     FastAPI backend
            |
      SQLAlchemy ORM
            |
    PostgreSQL / PostGIS
            ^
            |
     Alembic migrations

scripts/seed_demo.py --> isolated demo database
```

GitHub contains the **application code, models, migrations, assets, tests, and seed script**. It does **not** automatically contain the records held in each developer's PostgreSQL database. Each collaborator maintains their own local database.

## 2. Principal database tables

The main application tables identified during development are:

| Table | Role |
|---|---|
| `users` | Accounts, roles, password hashes, email verification and activation |
| `worker_profiles` | Worker profile information, occupation, city, availability and other public fields |
| `employer_profiles` | Business and private employer profiles |
| `jobs` | Job advertisements, categories, pay, status and ownership |
| `swipes` | Worker/employer Like or Pass decisions |
| `matches` | A mutual Like between a worker and an employer's job |
| `messages` | Stored chat messages belonging to a Match |

The exact schema may include additional supporting tables, such as categories, and fields introduced by later migrations. **Do not design new foreign keys based solely on this table summary.** Read the ORM models, migration files and generated schema SQL first.

### How the main concepts relate

- A **user** is either a worker or an employer and has a corresponding role-specific profile.
- An **employer** creates one or more **jobs**.
- A **worker** can discover and Like/Pass eligible jobs.
- Employers can review/discover eligible workers and Like/Pass them for jobs.
- Matching logic creates a **match** after the required reciprocal Likes.
- A **match** grants the relevant participants access to its **messages**.

The detailed **Entity–Relationship Diagram (ERD)** will be created separately from the actual schema after this guide is in place.

## 3. Local development prerequisites

Install Git, Docker Desktop (with Docker Compose), and a code editor. On macOS, the project has been developed using Python 3.12; Docker can supply the Python runtime for normal API execution and tests.

Clone the project:

```bash
git clone git@github.com:javahedi/DoppleJa_V1.git
cd DoppleJa_V1
git switch develop
```

> GitHub SSH access requires your **own** SSH key registered with your GitHub account and an accepted repository invitation. Alternatively use the HTTPS clone URL.

Start the services:

```bash
docker compose up -d --build
docker compose ps
```

The regular development app has previously been accessed at `http://127.0.0.1:8001/`. Confirm the actual port and settings in `compose.yaml`; do not assume that configuration is identical across machines.

## 4. Create an isolated demo database

**Never reset or overwrite another developer's database.** Use the dedicated database `doppleja_v1_demo` for synthetic local sample data.

Create it **only if it does not exist**:

```bash
docker compose exec db sh -lc \
  'psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '\''doppleja_v1_demo'\''" | grep -qx 1 || createdb -U "$POSTGRES_USER" doppleja_v1_demo'
```

Apply schema migrations:

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_demo \
  api alembic upgrade head
```

### Seed synthetic accounts and jobs

The maintained seeder is at **`scripts/seed_demo.py`**. In the current Compose setup this file may not automatically be visible inside the API container; copy it in before running it:

```bash
docker compose cp scripts/seed_demo.py api:/code/seed_demo.py

docker compose exec -e POSTGRES_DB=doppleja_v1_demo \
  api python /code/seed_demo.py
```

A successful earlier run reported:

| Content | Initial seed count |
|---|---:|
| Employer accounts | 50 |
| Worker accounts | 100 |
| Total users | 150 |
| Job postings | 100 |
| Matches | 25 |
| Messages | 54 |

These are **initial seed figures**. They are not live counts and may change when developers swipe, post jobs or send messages. Seed-generated records are illustrative and must not be represented as genuine applicants or employers.

**Do not run a seeder against the normal development, staging or production database.** Inspect the script's database-name safety check and environment variables before executing it.

### Demo logins (local testing only)

| Role | Email | Password |
|---|---|---|
| Worker | `worker001@example.com` | `Demo2026!` |
| Worker | `worker002@example.com` | `Demo2026!` |
| Employer | `employer01@example.com` | `Demo2026!` |
| Employer | `employer02@example.com` | `Demo2026!` |

Demo credentials must **never** be used for production accounts. Generated demo accounts were seeded as email-verified to simplify testing; actual signup and email verification must still be tested separately.

### Launching a separate demo API (if needed)

The project has previously used port **8002** for an isolated demo instance. The following is the existing development pattern; verify the image's import path, container port, and environment values in your checkout:

```bash
docker compose run --rm --no-deps \
  -e POSTGRES_DB=doppleja_v1_demo \
  -p 127.0.0.1:8002:8001 api \
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8001
```

Then open `http://127.0.0.1:8002/`. If port 8002 is already occupied, stop the old demo instance before starting another. A separate demo instance can still depend on the running database/Redis services.

## 5. Inspect the database schema

A collaborator should inspect the real schema rather than rely on a verbal description.

List tables:

```bash
docker compose exec db sh -lc \
  'psql -U "$POSTGRES_USER" -d doppleja_v1_demo -c "\\dt"'
```

Inspect selected tables:

```bash
docker compose exec db sh -lc \
  'psql -U "$POSTGRES_USER" -d doppleja_v1_demo -c "\\d+ users"'

docker compose exec db sh -lc \
  'psql -U "$POSTGRES_USER" -d doppleja_v1_demo -c "\\d+ jobs"'
```

Export **schema only** to a reviewable text file:

```bash
mkdir -p docs/database

docker compose exec -T db sh -lc \
  'pg_dump -U "$POSTGRES_USER" -d doppleja_v1_demo --schema-only --no-owner --no-privileges' \
  > docs/database/schema.sql
```

Review `docs/database/schema.sql` before committing it; ensure it contains no unwanted information. This SQL export is **documentation**, not the deployment or upgrade procedure. **Alembic remains the source of truth for applying schema changes.** Never import `schema.sql` over an Alembic-managed environment merely to update it.

## 6. Verify the demo records

```bash
docker compose exec -T db sh -lc \
  'psql -U "$POSTGRES_USER" -d doppleja_v1_demo' <<'SQL'
SELECT COUNT(*) AS users FROM users;
SELECT COUNT(*) AS employers FROM employer_profiles;
SELECT COUNT(*) AS workers FROM worker_profiles;
SELECT COUNT(*) AS jobs FROM jobs;
SELECT COUNT(*) AS matches FROM matches;
SELECT COUNT(*) AS messages FROM messages;
SQL
```

If the counts are zero, first inspect the seeding command and its error output; **do not drop the database automatically**. If you get a foreign-key error, inspect the order in which the seed script creates users and profiles. The corrected `scripts/seed_demo.py` includes `session.flush()` after creating each user before adding their profile.

## 7. Tests

Run the existing automated tests against the dedicated test database, **not the demo database**:

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test \
  api python -m pytest tests/ -v --tb=short
```

A previous full suite passed 25 tests, but this is **not** a guaranteed current test count. Follow the current repository test output and GitHub Actions result.

Before proposing a database change, check that migrations apply to a fresh database and that relevant tests still pass.

## 8. Rules for collaborative database development

1. **Each developer uses their own local PostgreSQL database.** Do not share credentials to someone's local database and do not sync Docker volumes through Git.
2. **Never commit secrets or real user records.** Do not push `.env`, SQL data dumps containing account information, PostgreSQL data directories or production passwords.
3. **Schema changes require Alembic migrations.** Modify ORM models and create/review the migration; do not change shared schemas manually with ad hoc `ALTER TABLE` commands.
4. **All changes go through feature branches and pull requests.** Contributors must not push directly to `develop` or `main`.
5. **The repository owner (`javahedi`) has final approval authority.** No contributor should merge a pull request without the owner's approval. Enforce this with suitable GitHub permissions and branch rules; documentation alone does not technically prevent merges.
6. **Run tests and verify the migration.** Include test results, migration instructions and rollback considerations in the pull request.
7. **After a migration is approved and merged**, everyone pulls `develop` and runs `alembic upgrade head` against their own applicable local databases.
8. **Share deterministic seed scripts, not live databases.** Keep synthetic sample profiles clearly labeled as demo content.

Example contributor workflow:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/database-example

# Make a focused change, write migration and tests.

docker compose exec -e POSTGRES_DB=doppleja_v1_test \
  api python -m pytest tests/ -v --tb=short

git add backend/ tests/
git commit -m "feat: describe database change"
git push -u origin feature/database-example
```

The contributor then opens a PR **into `develop`**, provides test results, and waits for the repository owner's review and merge decision. Avoid blindly using `git add .` for projects with local backups, generated files or untracked secrets.

## 9. Recommended repository documentation

```text
DoppleJa_V1/
├── backend/                 # FastAPI, ORM models, migrations integration
├── frontend/                # User interface and image assets
├── scripts/
│   └── seed_demo.py         # Maintained synthetic dataset generator
├── tests/
├── docs/
│   ├── database/
│   │   ├── DATABASE_GUIDE.md
│   │   ├── schema.sql       # Optional reviewed schema-only export
│   │   └── ERD.md           # Planned: generated from actual schema
│   └── development-history/
├── compose.yaml
├── alembic.ini
└── README.md
```

## 10. Next step: verified ERD

The **DoppleJa Entity–Relationship Diagram** should be generated from actual database constraints or ORM metadata. Before drawing it, inspect `schema.sql` or the SQLAlchemy models to establish table names, columns, primary keys, foreign keys, cardinalities and any uniqueness constraints. Do **not** invent relationships.

This guide is the starting point for onboarding collaborators. The ERD is intentionally a separate deliverable.
