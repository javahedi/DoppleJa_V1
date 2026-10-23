# DoppleJa Phase 4B — Real-time Chat (WebSockets)

A minimal overlay on the **completed Phase 4A** backend. No schema changes, no Alembic migration, no new Python package, no extra Docker service. **This version is single-process only** (your existing Docker Uvicorn development setup uses one API worker). Preserve the Phase 4A REST endpoints and PostgreSQL messages.

## New endpoint

`WS /ws/matches/{match_id}` — requires existing `doppleja_session` HttpOnly cookie from login and membership in the given match. It accepts JSON `{"type":"message","content":"Hallo!"}`. It sends `{"type":"message","message":{...stored PostgreSQL message...}}` to connected participants; invalid content gets a `type:error` response. Sending through the existing REST POST also broadcasts to connected clients.

Only the worker and the employer who owns the matched job have access. Credentials are **not** passed as URL query parameters. The server checks allowed Origin headers (`WS_ALLOWED_ORIGINS`) and rechecks match access before each message. Slow clients can catch up via `GET /api/matches/{match_id}/messages`.

## Install

1. Complete/commit Phase 4A, and work on clean `develop`:

   ```bash
   cd ~/Desktop/DoppleJa_V1
   git switch develop
   git status --short
   ```

2. Download `DoppleJa_Phase4B_Realtime.zip` to `~/Downloads`, then:

   ```bash
   unzip -o ~/Downloads/DoppleJa_Phase4B_Realtime.zip -d .
   ```

3. No migration is needed. The Python files are bind-mounted into Docker during development, so automatic reload usually applies them. Check:

   ```bash
   docker compose up -d
   docker compose logs --tail=30 api
   ```

4. Execute the test suite against **only** the isolated test database:

   ```bash
   docker compose exec -e POSTGRES_DB=doppleja_v1_test api \
      python -m pytest tests/ -v --tb=short
   ```

5. For local browser test, login at `http://127.0.0.1:8001/docs` (same hostname, not `localhost`) as the worker or employer, open browser Developer Tools Console **in that tab**, then paste:

   ```javascript
   const matchId = '98bd784b-815f-40e9-b01e-d292b0c5a3a5';
   const ws = new WebSocket(`ws://${location.host}/ws/matches/${matchId}`);
   ws.onopen = () => console.log('DoppleJa websocket connected');
   ws.onmessage = e => console.log('DoppleJa:', JSON.parse(e.data));
   ws.onclose = e => console.log('WebSocket closed:', e.code);
   // After connection:
   ws.send(JSON.stringify({type:'message', content:'Hallo live!'}));
   ```

   For a two-sided test, open a **separate private browser window/profile** and log in as the other participant. Open its console and connect with the same snippet. You should see new messages immediately in both windows. You can also send a message via Swagger's REST endpoint and watch it appear in the WebSocket console.

6. Commit/push only after tests pass:

   ```bash
   git add backend/app/main.py backend/app/modules/chat/router.py \
       backend/app/modules/chat/realtime.py tests/test_realtime.py
   git diff --cached --check
   git commit -m 'feat: add authenticated real-time chat websocket'
   git push origin develop
   ```

## Important limits before production

- WebSocket connections are held in memory **within one API process**. When deploying with multiple Uvicorn workers or multiple instances, replace local notifications with Redis pub/sub (already in your stack).
- HTTPS/WSS is required in production. Set `WS_ALLOWED_ORIGINS=https://YOUR_DOMAIN` and `AUTH_COOKIE_SECURE=true`. Nginx must forward `Upgrade`/`Connection` and use HTTP/1.1 for `/ws/`.
- REST API stays the source for retrieving historical messages and catching up after reconnect; the future mobile frontend should reconnect and reload history.
- Cookie-based write operations require a CSRF protection strategy before public launch, and rate limits and abuse controls should be added.
- This overlay does not add message read receipts, attachments, notifications, or a new database migration.
