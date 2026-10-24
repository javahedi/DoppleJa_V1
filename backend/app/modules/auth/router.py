import os
from uuid import UUID
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.modules.auth import service
from backend.app.modules.auth.schemas import LoginRequest, MessageOut, RegisterRequest, ResendVerificationRequest, UserOut
from backend.app.modules.auth.security import COOKIE_NAME, make_session, read_session

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageOut, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    service.register(db, body.email, body.password, body.role)
    return {"message": "Account created. Please verify your email."}


@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(body: ResendVerificationRequest, db: Session = Depends(get_db)):
    service.resend_verification(db, body.email)
    return {"message": "If the address has an unverified account, a verification email may be sent."}


@router.get("/verify-email", response_model=MessageOut)
def verify_email(token: str, db: Session = Depends(get_db)):
    service.verify_email(db, token)
    return {"message": "Email verified. You can now log in."}


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = service.authenticate(db, body.email, body.password)
    response.set_cookie(
        key=COOKIE_NAME,
        value=make_session(user.id),
        httponly=True,
        secure=os.getenv("AUTH_COOKIE_SECURE", "true").lower() == "true",
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )
    return user


def current_user(session: str | None = Cookie(default=None, alias=COOKIE_NAME), db: Session = Depends(get_db)) -> User:
    user_id = read_session(session) if session else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active or user.email_verified_at is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", samesite="lax")
    return {"message": "Logged out"}
