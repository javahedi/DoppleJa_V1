
import os
from html import escape
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.modules.auth import service
from backend.app.modules.auth.schemas import (
    LoginRequest,
    MessageOut,
    RegisterRequest,
    ResendVerificationRequest,
    UserOut,
)
from backend.app.modules.auth.security import (
    COOKIE_NAME,
    make_session,
    read_session,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECURE_PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'none'; "
        "style-src 'unsafe-inline'; "
        "form-action 'self'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'"
    ),
}


@router.post("/register", response_model=MessageOut, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    service.register(db, body.email, body.password, body.role)
    return {"message": "Account created. Please verify your email."}


@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    service.resend_verification(db, body.email)
    return {
        "message": (
            "If the address has an unverified account, "
            "a verification email may be sent."
        )
    }


@router.get("/verify-email", response_class=HTMLResponse)
def verification_confirmation(token: str):
    # Email scanners may open GET links automatically.
    # This endpoint must never activate an account.
    return HTMLResponse(
        content=_verification_page(
            "E-Mail bestätigen",
            "Bitte bestätige deine E-Mail-Adresse mit einem Klick.",
            token=token,
        ),
        headers=SECURE_PAGE_HEADERS,
    )


@router.post("/verify-email", response_class=HTMLResponse)
def verify_email(
    token: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        service.verify_email(db, token)
    except HTTPException as exc:
        if exc.status_code != 400:
            raise

        return HTMLResponse(
            content=_verification_page(
                "Link ungültig oder abgelaufen",
                "Bitte fordere über die Anmeldung eine "
                "neue Bestätigungs-E-Mail an.",
            ),
            status_code=400,
            headers=SECURE_PAGE_HEADERS,
        )

    return HTMLResponse(
        content=_verification_page(
            "E-Mail bestätigt!",
            "Dein Konto ist jetzt aktiv. Du kannst dich anmelden.",
            success=True,
        ),
        headers=SECURE_PAGE_HEADERS,
    )


def _verification_page(
    title: str,
    detail: str,
    token: str | None = None,
    success: bool = False,
) -> str:
    if token is not None:
        safe_token = escape(token, quote=True)

        control = (
            '<form method="post" action="/api/auth/verify-email">'
            '<input type="hidden" name="token" '
            f'value="{safe_token}">'
            '<button type="submit">E-Mail bestätigen</button>'
            '</form>'
        )
    else:
        control = '<a class="link" href="/">Zur Anmeldung</a>'

    mark = "✓" if success else "✦"

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>{escape(title)} · DoppleJa</title>
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box}}
body{{
    margin:0;
    min-height:100vh;
    display:grid;
    place-items:center;
    background:radial-gradient(
        circle at 25% 15%,#30214d,#12111d 65%
    );
    color:#f5f0e9;
    font:16px/1.6 system-ui,sans-serif;
    padding:24px;
}}
main{{
    width:min(100%,460px);
    text-align:center;
    border:1px solid #6f607d;
    padding:42px 30px;
    border-radius:24px;
    background:#21192f;
    box-shadow:0 18px 80px #09051280;
}}
.brand{{
    font-size:28px;
    font-weight:800;
    letter-spacing:.05em;
    color:#e8d5ac;
}}
.mark{{
    margin:24px auto 0;
    font-size:35px;
    color:#e8d5ac;
}}
h1{{
    font-size:27px;
    line-height:1.3;
    margin:15px 0 10px;
}}
p{{
    color:#d5cbd9;
    margin:0 0 26px;
}}
button,.link{{
    display:inline-block;
    min-width:180px;
    border:0;
    border-radius:14px;
    padding:13px 22px;
    background:#e8d5ac;
    color:#21192f;
    font:600 16px system-ui,sans-serif;
    text-decoration:none;
    cursor:pointer;
}}
button:hover,.link:hover{{
    background:#f7e6c3;
}}
</style>
</head>
<body>
<main>
    <div class="brand">DoppleJa</div>
    <div class="mark">{mark}</div>
    <h1>{escape(title)}</h1>
    <p>{escape(detail)}</p>
    {control}
</main>
</body>
</html>"""


@router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
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


def current_user(
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    user_id = read_session(session) if session else None
    user = db.get(User, user_id) if user_id else None

    if (
        user is None
        or not user.is_active
        or user.email_verified_at is None
    ):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        samesite="lax",
    )
    return {"message": "Logged out"}
