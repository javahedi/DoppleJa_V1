import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models import User
from backend.app.modules.auth import service


@pytest.fixture
def make_logged_in_user(monkeypatch):
    links = []
    users = []
    monkeypatch.setattr(service, "send_verification_email", lambda email, link: links.append(link))

    def create(role):
        email = f"employer-test-{uuid.uuid4().hex}@example.org"
        client = TestClient(app)
        users.append((client, email))
        assert client.post("/api/auth/register", json={"email": email, "password": "Strong-passphrase-123", "role": role}).status_code == 201
        token = parse_qs(urlparse(links.pop()).query)["token"][0]
        assert client.post("/api/auth/verify-email", data={"token": token}).status_code == 200
        assert client.post("/api/auth/login", json={"email": email, "password": "Strong-passphrase-123"}).status_code == 200
        return client

    yield create

    for client, email in users:
        client.close()
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                db.delete(user)
                db.commit()


def test_private_employer_profile(make_logged_in_user):
    client = make_logged_in_user("employer")
    assert client.get("/api/employers/me").status_code == 404
    payload = {"employer_type": "private", "display_name": "Max Müller", "city": "Berlin", "category": "Malerarbeiten", "description": "Suche Maler für zwei Tage"}
    r = client.put("/api/employers/me", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["employer_type"] == "private"
    assert r.json()["display_name"] == "Max Müller"
    assert client.get("/api/employers/me").json()["city"] == "Berlin"
    payload["city"] = "Potsdam"
    assert client.put("/api/employers/me", json=payload).json()["city"] == "Potsdam"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/employers/me").status_code == 401


def test_business_employer_profile(make_logged_in_user):
    client = make_logged_in_user("employer")
    r = client.put("/api/employers/me", json={"employer_type": "business", "display_name": "Nord Café", "category": "Restaurant & Café", "city": "Düsseldorf"})
    assert r.status_code == 200, r.text
    assert r.json()["employer_type"] == "business"
    assert r.json()["category"] == "Restaurant & Café"
    assert client.put("/api/employers/me", json={"employer_type": "invalid", "display_name": "Test"}).status_code == 422
    assert client.put("/api/employers/me", json={"employer_type": "private", "display_name": "  "}).status_code == 422


def test_worker_cannot_create_employer_profile(make_logged_in_user):
    client = make_logged_in_user("worker")
    r = client.put("/api/employers/me", json={"employer_type": "private", "display_name": "Max Müller"})
    assert r.status_code == 403
    assert client.get("/api/employers/me").status_code == 403
