import os
import re
import uuid
from urllib.parse import parse_qs, urlparse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User
from backend.app.modules.auth import service


@pytest.fixture
def account(monkeypatch):
    # Tests run against the dedicated test database provided by CI / Docker.
    address = f"test-{uuid.uuid4().hex}@example.org"
    links = []
    monkeypatch.setattr(service, "send_verification_email", lambda email, link: links.append(link))
    with TestClient(app) as client:
        yield client, address, links
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == address))
        if user:
            db.delete(user)
            db.commit()


def signup(client, email):
    return client.post("/api/auth/register", json={"email": email, "password": "Strong-passphrase-123", "role": "worker"})


def test_register_verify_login_me_logout(account):
    client, email, links = account
    assert client.get("/api/auth/me").status_code == 401
    response = signup(client, email)
    assert response.status_code == 201, response.text
    assert len(links) == 1
    assert signup(client, email).status_code == 409
    assert client.post("/api/auth/login", json={"email": email, "password": "Strong-passphrase-123"}).status_code == 403
    token = parse_qs(urlparse(links[0]).query)["token"][0]
    assert client.post("/api/auth/verify-email", data={"token": token}).status_code == 200
    assert client.post("/api/auth/verify-email", data={"token": token}).status_code == 400
    wrong = client.post("/api/auth/login", json={"email": email, "password": "incorrect"})
    assert wrong.status_code == 401
    logged_in = client.post("/api/auth/login", json={"email": email, "password": "Strong-passphrase-123"})
    assert logged_in.status_code == 200, logged_in.text
    assert logged_in.json()["role"] == "worker"
    assert client.get("/api/auth/me").json()["email"] == email
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_invalid_registration(account):
    client, email, _ = account
    assert client.post("/api/auth/register", json={"email": email, "password": "short", "role": "worker"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": email, "password": "Strong-passphrase-123", "role": "admin"}).status_code == 422
