import os
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from jwt import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher()
COOKIE_NAME = "doppleja_session"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def make_session(user_id: UUID) -> str:
    secret = os.environ["AUTH_SECRET_KEY"]
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + timedelta(days=7), "iss": "doppleja", "type": "session"}, secret, algorithm="HS256")


def read_session(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, os.environ["AUTH_SECRET_KEY"], algorithms=["HS256"], issuer="doppleja", options={"require": ["sub", "exp", "iat", "iss", "type"]})
        if payload.get("type") != "session":
            return None
        return UUID(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError):
        return None
