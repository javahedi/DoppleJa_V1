# DoppleJa Phase 5.1B — Worker Likes

This overlay is intended to install **after Phase 5.1A** on branch `develop`.
No migration or new table is needed. Existing `swipes`, `jobs`, `matches` provide the data.

## 1. Verify clean branch, then extract

```bash
cd ~/Desktop/DoppleJa_V1
git switch develop
git status --short
unzip -o ~/Downloads/DoppleJa_Phase5_1B_WorkerLikes.zip -d .
```

## 2. Register the new API router

```bash
python3 scripts/install_phase5_1b.py
python3 -m py_compile backend/app/main.py backend/app/modules/likes/router.py
node --check frontend/js/app.js
```

No Docker rebuild is needed if the FastAPI backend and frontend directories are mounted. Otherwise: `docker compose up -d --build api`.

## 3. Automated test in isolated DB

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short
```

## 4. Manual acceptance

1. Login as worker `user@example.com`, verify bottom tab **Meine Likes**.
2. Existing **Servicekraft (m/w/d)** Like must appear with **Match** and button **Zum Chat**.
3. Like the **Maler** job (if still active and not previously swiped), then verify it appears as **Warten** until the employer likes back.
4. Use a **disposable job**, like it from the worker, then pause it as the owner. Worker sees **Nicht mehr verfügbar**. Reactivate it: if not matched, its status returns to **Warten**.
5. Login as employer: GET `/api/workers/me/likes` should return 403; employer navigation remains unchanged.
6. No pass/dislike jobs should appear in the likes list.

**Do not archive your existing Servicekraft/Nord Café job just for testing.**

## 5. Commit only if everything passes

```bash
git add backend/app/main.py backend/app/modules/likes scripts/install_phase5_1b.py frontend/js/app.js frontend/css/styles.css tests/test_worker_likes.py
git diff --cached --check
git commit -m "feat: add worker liked jobs history"
git push origin develop
```
Check GitHub Actions status, then proceed to Phase 5.2 premium UI redesign.

### Notes

- For status precedence, a paused or archived job shows **Nicht mehr verfügbar**, even if it was previously matched. The underlying match/chat records remain preserved.
- The endpoint lists up to 200 latest worker Likes. Pagination can be added when needed.
- This is only a worker's Like history, not a bookmark/save-for-later feature.
