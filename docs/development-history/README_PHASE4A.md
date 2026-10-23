# DoppleJa V1 — Phase 4A: Private text chat

This is a **drop-in overlay** for your completed Phase 3C project. It does not overwrite old migrations, wipe Docker volumes, or modify users/jobs/matches.

## New functionality
- `GET /api/chats` — my matches with each conversation's most recent message (null until first message)
- `GET /api/matches/{match_id}/messages?limit=50&offset=0` — chronological messages (max 100 per request)
- `POST /api/matches/{match_id}/messages` — send `{ "content": "Hallo!" }` (1–2000 nonblank characters)
- Only the matched worker and the job-owning employer may view/send. Everyone else gets 404.
- HTTP polling for now; WebSockets and notifications later.

## Install
1. Verify Phase 3C tests passed, and commit/push Phase 3C to `develop` first.
2. `cd ~/Desktop/DoppleJa_V1 && git switch develop && git status --short`
3. Make sure git status is empty. Extract **the contents** of this archive into the project root (the ZIP paths start with `backend/` and `tests/`). For example: `unzip -o ~/Downloads/DoppleJa_Phase4A_Chat.zip -d .`
4. Inspect migration `backend/alembic/versions/e41a9b7c620d_create_messages.py`.
5. `docker compose exec api python -m alembic -c alembic.ini upgrade head`
6. `docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m alembic -c alembic.ini upgrade head`
7. `docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short`
8. Test via Swagger as both users; see below.
9. `git add backend/app/main.py backend/app/models/__init__.py backend/app/models/message.py backend/app/modules/chat backend/alembic/versions/e41a9b7c620d_create_messages.py tests/test_chat.py && git diff --cached --check && git commit -m "feat: add private match chat" && git push origin develop`

## Existing Nord Café match — manual test

Match ID: `98bd784b-815f-40e9-b01e-d292b0c5a3a5`

1. In `http://127.0.0.1:8001/docs`, log in as the verified worker `user@example.com` using the password you originally set.
2. Call `POST /api/matches/98bd784b-815f-40e9-b01e-d292b0c5a3a5/messages` with `{ "content": "Hallo Nord Café!" }`. Expect `201`.
3. Call `GET /api/matches/98bd784b-815f-40e9-b01e-d292b0c5a3a5/messages`. Expect the message.
4. Logout, login with `business@example.com` (Nord Café), using its original password. Send `{ "content": "Hallo! Wann kannst du anfangen?" }` to same endpoint. Expect `201`.
5. Call `GET /api/chats` as either account, and see the last message. `GET /api/matches/{match_id}/messages` should now contain two messages.
6. A different employer account cannot view or send messages for this match (404).

## Notes
- Keep dev and integration tests separate: `POSTGRES_DB=doppleja_v1_test` only for Pytest.
- Database migration adds only `messages` and its index. No data is deleted.
- Every request is authenticated using existing session cookie; no user-selected `sender_id`.
- This package is a development baseline. Before public launch add CSRF defenses for cookie auth, rate limiting, blocking/reporting, anti-spam, and audit/retention controls. Avoid exposing verification tokens in production logs.
- Versioned file naming follows your previous packages.
