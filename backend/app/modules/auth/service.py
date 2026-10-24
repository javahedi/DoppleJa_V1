import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import User, VerificationToken
from backend.app.modules.auth.security import hash_password, verify_password


def utcnow():
    return datetime.now(timezone.utc)


def normalized_email(email: str) -> str:
    return email.strip().lower()


def send_verification_email(to_email: str, link: str) -> None:
    # Local development only: link appears in Docker logs.
    if os.getenv("AUTH_DEV_PRINT_LINK") == "true":
        print(f"[DEV ONLY] Verification link for {to_email}: {link}", flush=True)
        return
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM must be configured outside development")
    message = EmailMessage()
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(domain="doppleja.de")
    message["Subject"] = "DoppleJa – E-Mail bestätigen"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(f"Bitte bestätige deine E-Mail-Adresse:\n\n{link}\n\nDieser Link ist 30 Minuten gültig.")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
        import ssl
        smtp.starttls(context=ssl.create_default_context())
        if os.getenv("SMTP_USERNAME"):
            smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


def register(db: Session, email: str, password: str, role: str) -> None:
    address = normalized_email(email)
    if db.scalar(select(User.id).where(User.email == address)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=address, password_hash=hash_password(password), role=role)
    raw_token = secrets.token_urlsafe(32)
    verification = VerificationToken(user_id=user.id, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=utcnow() + timedelta(minutes=30))
    # UUID defaults run on INSERT; flush user first so foreign key has a concrete value.
    try:
        db.add(user)
        db.flush()
        verification.user_id = user.id
        db.add(verification)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None
    link = os.environ["PUBLIC_API_URL"].rstrip("/") + "/api/auth/verify-email?token=" + quote(raw_token)
    try:
        send_verification_email(address, link)
    except (OSError, smtplib.SMTPException, RuntimeError) as exc:
        # Account exists unverified; the resend route can recover when mail is back.
        # Never expose SMTP credentials or downstream error details to callers.
        raise HTTPException(status_code=503, detail="Verification email unavailable. Please request a new link shortly.") from None


def verify_email(db: Session, token: str) -> None:
    if len(token) > 256:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = db.scalar(select(VerificationToken).where(VerificationToken.token_hash == token_hash).with_for_update())
    if not record or record.used_at or record.expires_at <= utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification link")
    user.email_verified_at = utcnow()
    record.used_at = utcnow()
    db.commit()


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == normalized_email(email)))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if user.email_verified_at is None:
        raise HTTPException(status_code=403, detail="Verify your email first")
    return user


# Phase 6.1A — email verification recovery.
# These limits prevent repeated resend for one existing account. Network/IP-wide
# rate limiting is a separate public-launch gate (Phase 6.1B).
RESEND_COOLDOWN_SECONDS = 90
MAX_VERIFICATION_TOKENS_PER_USER = 20


def resend_verification(db: Session, email: str) -> None:
    """Request an email without revealing whether an account exists.

    An email is only attempted for a real, active, unverified user. The new
    token is stored before delivery so it is valid immediately if received;
    existing tokens remain usable until expiry if SMTP is unavailable.
    """
    address = normalized_email(email)
    user = db.scalar(select(User).where(User.email == address).with_for_update())
    if user is None or not user.is_active or user.email_verified_at is not None:
        return
    now = utcnow()
    recent = db.scalar(
        select(VerificationToken)
        .where(VerificationToken.user_id == user.id)
        .order_by(VerificationToken.created_at.desc(), VerificationToken.id.desc())
        .limit(1)
    )
    if recent is not None and recent.created_at is not None:
        if recent.created_at > now - timedelta(seconds=RESEND_COOLDOWN_SECONDS):
            return
    # Bound token accumulation for a single account. Avoid deleting unexpired
    # prior tokens; they may be needed after a transient SMTP failure.
    from sqlalchemy import func
    count = db.scalar(select(func.count(VerificationToken.id)).where(
        VerificationToken.user_id == user.id,
        VerificationToken.expires_at > now,
        VerificationToken.used_at.is_(None),
    )) or 0
    if count >= MAX_VERIFICATION_TOKENS_PER_USER:
        return
    raw_token = secrets.token_urlsafe(32)
    db.add(VerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=now + timedelta(minutes=30),
    ))
    db.commit()
    link = os.environ["PUBLIC_API_URL"].rstrip("/") + "/api/auth/verify-email?token=" + quote(raw_token)
    try:
        send_verification_email(address, link)
    except (OSError, smtplib.SMTPException, RuntimeError):
        # A rejected/undelivered send must not enumerate account existence.
        # Retain token since SMTP may have accepted the message just before error.
        pass
