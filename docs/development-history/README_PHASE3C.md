# DoppleJa V1 — Phase 3C: Mutual Matches

This overlay builds on **Phase 3B** (`7c91d4e5a602`) and retains your development data.

## Features

- Automatic match on the second Like for a `(job_id, worker_id)` pair.
- Worker-first and employer-first work identically.
- A transaction-level PostgreSQL advisory lock per pair prevents concurrent Likes from missing a match.
- Unique database constraint prevents duplicate matches.
- Existing identical swipe requests are idempotent and can reconcile a missing match.
- Existing mutual Likes (including Nord Café) are backfilled by the migration.
- `GET /api/matches` and `GET /api/matches/{match_id}` require authentication and enforce ownership.
- The existing `POST /api/swipes` response adds `is_match` and `match_id` fields; existing fields remain unchanged.

## Install on Mac

1. Before extracting, verify `git switch develop` and `git status --short` is empty. Ensure Phase 3B is committed.
2. From `~/Desktop/DoppleJa_V1`: `unzip -o ~/Downloads/DoppleJa_Phase3C_Matching.zip -d .`
3. Check `docker compose exec api python -m alembic -c alembic.ini current` (should show `7c91d4e5a602`).
4. Review `backend/alembic/versions/d64f1a2c9b30_create_matches.py`. The **upgrade** only creates the `matches` table, two indexes, and inserts existing mutual Likes. No existing tables are dropped or truncated.
5. Run `docker compose exec api python -m alembic -c alembic.ini upgrade head`.
6. Run `docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m alembic -c alembic.ini upgrade head`.
7. Run `docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short`.
8. In Swagger `http://127.0.0.1:8001/docs`, login as worker and `GET /api/matches`; log in as the Nord Café employer and repeat. Both should see the previously-mutual match.
9. Check backfill in PostgreSQL:

   ```bash
   docker compose exec db psql -U doppleja_v1 -d doppleja_v1 \
     -c "SELECT m.id, m.job_id, m.worker_id, m.created_at FROM matches m ORDER BY m.created_at DESC LIMIT 10;"
   ```

10. After successful tests, commit only the Phase 3C files:

   ```bash
   git add backend/app/main.py backend/app/models/__init__.py \
     backend/app/models/match.py backend/app/modules/matching \
     backend/app/modules/swipes/router.py backend/app/modules/swipes/schemas.py \
     backend/alembic/versions/d64f1a2c9b30_create_matches.py \
     tests/test_matches.py
   git diff --cached --check
   git commit -m "feat: automatically match reciprocal likes"
   git push origin develop
   ```

## Notes

- Does not create chat yet — that is Phase 4.
- Does not touch the old `DoppleJa` project.
- `docker compose up -d` if containers are stopped; since Python code is mounted and auto-reloaded, you do not need a rebuild for this overlay.
- Never run tests without explicitly choosing the `_test` database.
- `POST /api/swipes` returns `is_match=true` with `match_id` once both have liked.
- Running `downgrade` would delete all stored matches; do not do that.
