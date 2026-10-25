"""API-level checks that do not touch the normal development database."""
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.modules.moderation.router import router, photo_identifier
from backend.app.modules.media.security import PREFIX
from backend.app.modules.auth.router import current_user
from backend.app.core.database import get_db


def test_bad_photo_identifiers_rejected():
    for val in ('https://attacker.invalid/x.png', PREFIX+'../x.webp', PREFIX+'b'*32+'.jpg', PREFIX+'a'*32+'.webp?x=1'):
        with pytest.raises(Exception):
            photo_identifier(val)


def test_reporting_requires_login():
    app = FastAPI()
    app.include_router(router)
    result = TestClient(app).post('/api/moderation/photo-reports', json={
        'photo_url': PREFIX+'a'*32+'.webp', 'reason': 'impersonation'})
    assert result.status_code in (401, 403)


def test_reporting_validates_reason_before_database():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[current_user] = lambda: type('UserStub', (), {'id': uuid4()})()
    app.dependency_overrides[get_db] = lambda: None
    result = TestClient(app).post('/api/moderation/photo-reports', json={
        'photo_url': PREFIX+'a'*32+'.webp', 'reason': 'nonsense'})
    assert result.status_code == 422


def test_reporting_rejects_foreign_host_and_path_traversal_before_database():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[current_user] = lambda: type('UserStub', (), {'id': uuid4()})()
    app.dependency_overrides[get_db] = lambda: None
    for url in ('https://attacker.invalid/cat.png', PREFIX+'../etc/passwd.webp'):
        result = TestClient(app).post('/api/moderation/photo-reports', json={'photo_url':url, 'reason':'other'})
        assert result.status_code == 422
