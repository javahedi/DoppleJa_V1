# DoppleJa — Phase 5.1A: Employer Job Management

**Only install this phase.** Verify it before proceeding to 5.1B or 5.2.

This overlay is based on the Phase 5 frontend and Phase 3A/3B backend packages. It updates four existing files, adds one migration and one test. It does not replace the authentication, chat, matching, or employer modules.

## Behavior

- Employer tab **Meine Jobs** lists all owned jobs (active, paused, archived).
- **Bearbeiten** edits existing fields without changing active/paused state.
- **Pausieren** removes a listing from worker discovery.
- **Reaktivieren** makes a paused job discoverable again.
- **Archivieren** is a confirmed, irreversible soft delete. Keeps jobs, swipes, matches, and chat history in the DB. No hard delete.
- Only the job owner may perform these operations. Archived jobs cannot be modified.

## Install

```bash
cd ~/Desktop/DoppleJa_V1
git switch develop
git status --short    # MUST be empty, commit current work first
unzip -o ~/Downloads/DoppleJa_Phase5_1A_EmployerJobs.zip -d .
docker compose exec api python -m alembic -c alembic.ini current
docker compose exec api python -m alembic -c alembic.ini heads
```

Expected old revision: e41a9b7c620d. New head: f5a1e0d701aa. Review migration before applying.

```bash
docker compose exec api python -m alembic -c alembic.ini upgrade head
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m alembic -c alembic.ini upgrade head
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short
```

Open http://127.0.0.1:8001/ and sign in as the existing employer. **Meine Jobs** bottom tab should display Servicekraft and Maler. Test each action on a disposable new job first, especially Archiving (irreversible). After pausing, confirm with a worker account that the job is gone from discovery; reactivate and check it returns.

Because the backend is bind-mounted and the frontend served from its own bind mount, a reload may be sufficient. If not: `docker compose up -d --build api`. In your browser use a hard reload if cached JS is shown.

After results pass:

```bash
git add backend/app/models/job.py backend/app/modules/jobs/router.py backend/app/modules/jobs/schemas.py backend/app/modules/swipes/router.py backend/alembic/versions/f5a1e0d701aa_archive_jobs.py frontend/js/app.js frontend/css/styles.css tests/test_job_management.py
git diff --cached --check
git commit -m "feat: manage employer jobs with edit pause and archive"
git push origin develop
```

**Stop here for verification.** Phase 5.1B Worker Likes comes only after test and screen results are checked.
