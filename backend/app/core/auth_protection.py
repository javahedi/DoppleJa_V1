"""DoppleJa auth protection: Redis-based throttling and browser request-origin checks.

Install via install_phase6_1b.py. Does not alter the Phase 6.1A API.
"""
import hashlib
import hmac
import json
import os
from urllib.parse import urlparse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# IP quotas and email quotas are deliberately independent; Redis ensures
# all API processes share counters. Windows are fixed (not sliding).
LIMITS = {
    "/api/auth/register": ((5, 600), (3, 3600)),
    "/api/auth/login": ((20, 600), (10, 900)),
    "/api/auth/resend-verification": ((5, 600), (3, 3600)),
}
MAX_BODY_BYTES = 8192


def allowed_origins():
    raw = os.getenv("AUTH_ALLOWED_ORIGINS", "http://testserver,http://127.0.0.1:8001,http://localhost:8001")
    values = {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}
    if os.getenv("AUTH_SECURITY_MODE", "development") == "production" and any(
        value.startswith("http://") for value in values
    ):
        raise RuntimeError("Production AUTH_ALLOWED_ORIGINS must use HTTPS")
    return values


def valid_origin(value, allowed):
    if not value:
        return False
    try:
        parsed = urlparse(value)
        candidate = f"{parsed.scheme}://{parsed.netloc}"
        return candidate in allowed and not parsed.username and not parsed.password
    except ValueError:
        return False


def _redis_client():
    # Lazy import: development test environments can load the module before
    # dependencies are rebuilt. Production must have redis installed.
    import redis
    return redis.Redis(host=os.getenv("REDIS_HOST", "redis"),
                       port=int(os.getenv("REDIS_PORT", "6379")),
                       socket_connect_timeout=1, socket_timeout=1,
                       decode_responses=True)


def _identity_hash(kind, text):
    secret = os.environ["AUTH_SECRET_KEY"].encode()
    return hmac.new(secret, f"{kind}:{text}".encode(), hashlib.sha256).hexdigest()


def _throttle(client, key, limit, seconds):
    # INCR + EXPIRE made atomic by Lua to avoid keys without expiry in a crash.
    count = client.eval(
        "local n=redis.call('INCR',KEYS[1]); "
        "if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n",
        1, key, seconds,
    )
    return int(count) <= limit


class AuthProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
            allowed = allowed_origins()
            origin = request.headers.get("origin")
            if origin and not valid_origin(origin, allowed):
                return JSONResponse({"detail": "Forbidden request origin"}, status_code=403)
            if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
                return JSONResponse({"detail": "Cross-site requests forbidden"}, status_code=403)
            # Requests bearing a session are security sensitive. Browser requests
            # should carry Origin or Referer, except synthetic TestClient requests.
            if "doppleja_session" in request.cookies:
                referer = request.headers.get("referer")
                if not origin and referer and not valid_origin(referer, allowed):
                    return JSONResponse({"detail": "Forbidden request referer"}, status_code=403)
                if (os.getenv("AUTH_SECURITY_MODE") == "production" and
                    not origin and not referer):
                    return JSONResponse({"detail": "Origin required"}, status_code=403)

        path = request.url.path
        if request.method == "POST" and path in LIMITS:
            raw = await request.body()
            if len(raw) > MAX_BODY_BYTES:
                return JSONResponse({"detail": "Request too large"}, status_code=413)
            try:
                obj = json.loads(raw)
                email = obj.get("email", "") if isinstance(obj, dict) else ""
            except (UnicodeDecodeError, ValueError):
                email = ""
            # Never accept arbitrary X-Forwarded-For; trust proxy is a Uvicorn
            # deployment decision, not a client-supplied header.
            ip = request.client.host if request.client else "unknown"
            (ip_limit, ip_period), (email_limit, email_period) = LIMITS[path]
            namespace = path.rsplit("/", 1)[-1]
            mode = os.getenv("AUTH_SECURITY_MODE", "development")
            try:
                redis_client = _redis_client()
                ip_key = f"dj:limit:{namespace}:ip:{_identity_hash('ip', ip)}"
                ok_ip = _throttle(redis_client, ip_key, ip_limit, ip_period)
                ok_email = True
                if isinstance(email, str) and email:
                    email_key = f"dj:limit:{namespace}:email:{_identity_hash('email', email.strip().lower())}"
                    ok_email = _throttle(redis_client, email_key, email_limit, email_period)
            except Exception:
                # Fail closed in production, rather than silently removing abuse
                # protection when Redis is unavailable.
                if mode == "production":
                    return JSONResponse({"detail": "Authentication temporarily unavailable"}, status_code=503)
                # Local development/test only: logs should warn when Redis missing.
                import logging
                logging.getLogger(__name__).warning("Auth rate limiting unavailable in development")
                ok_ip = ok_email = True
            if not (ok_ip and ok_email):
                return JSONResponse({"detail": "Too many requests. Try again later."},
                                    status_code=429, headers={"Retry-After": "600"})
        return await call_next(request)
