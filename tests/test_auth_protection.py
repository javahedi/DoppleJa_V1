"""Phase 6.1B checks. All requests use the existing auth endpoints."""
from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core import auth_protection


class FakeRedis:
    def __init__(self):
        self.counts = {}
    def eval(self, script, numkeys, key, seconds):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]


def test_rejects_cross_origin_and_fetch_metadata():
    with TestClient(app) as client:
        body = {"email": "abuse@example.org", "password": "Some-passphrase-123", "role": "worker"}
        assert client.post('/api/auth/register', json=body, headers={"Origin":"https://evil.example"}).status_code == 403
        assert client.post('/api/auth/register', json=body, headers={"Sec-Fetch-Site":"cross-site"}).status_code == 403

@pytest.mark.real_rate_limit
def test_registration_throttle(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(auth_protection, '_redis_client', lambda: fake)
    with TestClient(app) as client:
        # Invalid body: no account is created; limiter still applies.
        for i in range(5):
            status = client.post('/api/auth/register', json={"email": f"limit{i}@example.org", "password": "short", "role": "worker"}).status_code
            assert status == 422
        response = client.post('/api/auth/register', json={"email": "limit5@example.org", "password": "short", "role": "worker"})
        assert response.status_code == 429
        assert 'Retry-After' in response.headers
