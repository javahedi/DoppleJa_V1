"""GET is safe even if an email-provider scanner opens the verification URL."""
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User
from backend.app.modules.auth import service

@pytest.fixture
def confirmation_account(monkeypatch):
    email = f"confirmation-{uuid.uuid4().hex}@example.org"
    links = []
    monkeypatch.setattr(service, "send_verification_email", lambda address, link: links.append(link))
    with TestClient(app) as client:
        yield client, email, links
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()


class ConfirmationFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.actions = []
    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self.actions.append(dict(attrs))



def test_verification_get_does_not_consume_token(confirmation_account):
    client, email, links = confirmation_account

    password = "Strong-passphrase-123"

    # 1. Register a new account.
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "worker",
        },
    )
    assert response.status_code == 201

    token = parse_qs(urlparse(links[0]).query)["token"][0]

    # 2. Opening the email link must NOT activate the account.
    for _ in range(2):
        page = client.get(
            "/api/auth/verify-email",
            params={"token": token},
        )

        assert page.status_code == 200
        assert "text/html" in page.headers["content-type"]
        assert page.headers["cache-control"] == "no-store"
        assert page.headers["referrer-policy"] == "strict-origin-when-cross-origin"

        parser = ConfirmationFormParser()
        parser.feed(page.text)

        assert len(parser.actions) == 1
        assert parser.actions[0]["method"] == "post"
        assert parser.actions[0]["action"] == "/api/auth/verify-email"

    # 3. Login must still be blocked after GET.
    before_confirmation = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert before_confirmation.status_code == 403

    # 4. The deliberate POST activates the account.
    confirmed = client.post(
        "/api/auth/verify-email",
        data={"token": token},
    )
    assert confirmed.status_code == 200

    # 5. A verification token can only be used once.
    reused = client.post(
        "/api/auth/verify-email",
        data={"token": token},
    )
    assert reused.status_code == 400

    # 6. Login must succeed after confirmation.
    after_confirmation = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert after_confirmation.status_code == 200
