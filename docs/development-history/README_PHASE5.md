# DoppleJa V1 — Phase 5 Mobile Frontend

Vanilla HTML/CSS/JS, German-language, mobile-first UI. Backend APIs and authentication
are reused, not replaced. No database migration is required.

## Installation (from your Mac)

1. Commit Phase 4B first; ensure `git status --short` is clean on `develop`.
2. Download `DoppleJa_Phase5_Frontend.zip` into `~/Downloads`.
3. From `~/Desktop/DoppleJa_V1`, extract:

```bash
unzip -o ~/Downloads/DoppleJa_Phase5_Frontend.zip -d .
```

4. Install the FastAPI route and Docker bind mount (makes targeted, idempotent edits to
   `backend/app/main.py` and `compose.yaml`):

```bash
python3 scripts/install_phase5.py

docker compose config --quiet
docker compose up -d --build api
```

5. Open **http://127.0.0.1:8001/** (NOT `/docs`). Existing Swagger remains at `/docs`.
   No separate Uvicorn or frontend development server is necessary.

6. Tests (uses dedicated test DB for the existing integration tests):

```bash
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short
```

7. Commit and push on `develop` after tests:

```bash
git add frontend/ backend/app/main.py backend/app/modules/frontend/ compose.yaml scripts/install_phase5.py tests/test_frontend_files.py
git diff --cached --check
git commit -m "feat: add mobile-first vanilla JavaScript frontend"
git push origin develop
```

## Available pages

- Landing / worker-employer signup / login / verification instructions
- Worker and employer profile create/edit
- Worker job discovery and Like/Pass
- Employer own-job creation and candidate discovery for selected job, Like/Pass
- Matches list / chats list / live chat with REST fallback
- Account settings / logout

## Integration notes

- API uses same origin and `credentials: 'same-origin'`: HttpOnly session cookie works.
- WebSocket uses ws:// on localhost, wss:// when HTTPS is enabled. Nginx must forward
  WebSocket Upgrade/Connection headers in production.
- The original API doesn't provide employer name/photos in the job discovery result,
  or enriched match names. Cards show job, category and city; match rows display a
  short ID. This is intentional, NOT invented data. Add enriched API responses later.
- `photo_url` is stored but image uploads are not yet implemented. Current design uses
  styled emoji/illustrated backgrounds rather than untrusted remote image loads.
- Employer `GET /api/discovery/workers` currently returns a candidate list for a job.
- The WebSocket hub is still single-process; Redis fan-out is required before using
  multiple API workers.
- This is a **development MVP**, not production-ready. Before public launch add CSRF
  protection for cookie-authenticated state changes, abuse/rate limits, password
  reset and email delivery, GDPR/privacy controls, moderation/block/report flows,
  and CSP/security headers. Do not put test secrets into Git.
- Network fonts are progressive enhancement; system font fallback works offline.
