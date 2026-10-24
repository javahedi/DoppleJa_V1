# DoppleJa Phase 6.1A — Registration reliability overlay

**Target:** local Mac `~/Desktop/DoppleJa_V1`, branch `develop`. Never install directly on Hetzner.

## Scope

- Keep the existing registration, login, session and verification API compatible.
- Add `POST /api/auth/resend-verification` with generic, non-enumerating result.
- Resend cooldown (90s) per unverified account using DB token creation time, and limit accumulation.
- Recover when SMTP failed after user creation: resend remains available.
- Set `Date` and `Message-ID` email headers and verify SMTP peer certificate.
- Add automated tests for SMTP failure/retry, cooldown and email headers.

## Install on Mac (only after reviewing the diff)

From a CLEAN `develop` working tree, extract ZIP to a temporary folder (not over project yet). Compare using `diff -u`, then copy changed files (paths under this package) into your local `DoppleJa_V1` project. **Do not copy this README into the repo unless desired**.

Changed files:
- `backend/app/modules/auth/service.py`
- `backend/app/modules/auth/router.py`
- `backend/app/modules/auth/schemas.py`
- `tests/test_auth_phase6_1a.py` (new)

Commands:

```bash
cd ~/Desktop/DoppleJa_V1
node --check frontend/js/app.js
docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v --tb=short
git diff --check
git diff --stat
```

**Note:** Development Compose binds backend files. If dependencies / image differ, rebuild before testing. Read and review tests, then commit to `develop` only after green results. This package has **not** been exercised on your live Mac working tree.

## Known release blockers — NOT solved here

1. **Global abuse protection:** Redis-backed limits on register/login/resend by IP and normalized account, with correct trusted proxy handling. Database per-account cooldown alone is not enough.
2. **CSRF defense** for authenticated state-changing endpoints, and origin/host validation at Caddy/FastAPI. `SameSite=Lax` isn't sufficient by itself.
3. **GET verification link consumption:** existing GET endpoint changes account state; mail link-preview bots can prefetch it. Before public launch, replace with safe confirmation page and POST-based consume flow, including test changes and UX review.
4. **Duplicate-email account enumeration:** `/register` still returns 409. Review threat model and make responses generic where practical.
5. **Resend on initially failed SMTP:** a 90-second cooldown applies; improve UX to explain this. No guarantee a downstream SMTP accept equals inbox delivery.
6. **Persistent sessions:** JWT logout currently only deletes browser cookie. Review session revocation and password reset.
7. **Deployment setup:** Production changes made directly to VPS are not yet committed to repo. Secure env files must stay out of Git.

The website must **not** be publicly launched until the blockers are reviewed and applicable protections implemented and tested. The old Next.js/Caddy stack and mailserver remain unchanged by this overlay.
