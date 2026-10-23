import uuid
from urllib.parse import parse_qs, urlparse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User
from backend.app.modules.auth import service

@pytest.fixture
def logged_in_worker(monkeypatch):
    links = []
    monkeypatch.setattr(service, "send_verification_email", lambda email, link: links.append(link))
    email = f"worker-{uuid.uuid4().hex}@example.org"
    with TestClient(app) as client:
        assert client.post("/api/auth/register", json={"email":email,"password":"Strong-passphrase-123","role":"worker"}).status_code == 201
        token = parse_qs(urlparse(links[0]).query)["token"][0]
        assert client.get("/api/auth/verify-email", params={"token": token}).status_code == 200
        assert client.post("/api/auth/login", json={"email":email,"password":"Strong-passphrase-123"}).status_code == 200
        yield client
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()

def test_worker_profile_create_update_and_read(logged_in_worker):
    client = logged_in_worker
    assert client.get("/api/workers/me").status_code == 404
    payload = {"display_name":"Sara Müller", "profession":"Servicekraft", "city":"Düsseldorf", "availability":"Ab sofort", "bio":"Freundlich und zuverlässig"}
    response = client.put("/api/workers/me", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["profession"] == "Servicekraft"
    assert response.json()["display_name"] == "Sara Müller"
    assert client.get("/api/workers/me").json()["city"] == "Düsseldorf"
    payload["availability"] = "In 2 Wochen"
    assert client.put("/api/workers/me", json=payload).json()["availability"] == "In 2 Wochen"
    assert client.put("/api/workers/me", json={"display_name":"  "}).status_code == 422
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/workers/me").status_code == 401

def test_employer_cannot_edit_worker_profile(monkeypatch):
    links=[]
    monkeypatch.setattr(service, "send_verification_email", lambda email, link: links.append(link))
    email=f"employer-{uuid.uuid4().hex}@example.org"
    with TestClient(app) as client:
        assert client.post("/api/auth/register",json={"email":email,"password":"Strong-passphrase-123","role":"employer"}).status_code==201
        token=parse_qs(urlparse(links[0]).query)["token"][0]
        assert client.get("/api/auth/verify-email",params={"token":token}).status_code==200
        assert client.post("/api/auth/login",json={"email":email,"password":"Strong-passphrase-123"}).status_code==200
        assert client.put("/api/workers/me",json={"display_name":"Not a worker"}).status_code==403
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if user:
            db.delete(user)
            db.commit()
