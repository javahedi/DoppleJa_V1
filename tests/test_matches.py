"""Integration tests run only in the isolated *_test database."""
import uuid
from urllib.parse import parse_qs, urlparse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import Match, User
from backend.app.modules.auth import service


@pytest.fixture
def actors(monkeypatch):
    links = []
    accounts = []
    monkeypatch.setattr(service, 'send_verification_email', lambda email, link: links.append(link))

    def create(role):
        email = f'match-{uuid.uuid4().hex}@example.org'
        client = TestClient(app)
        accounts.append((client, email))
        assert client.post('/api/auth/register', json={
            'email': email, 'password': 'Strong-passphrase-123', 'role': role,
        }).status_code == 201
        token = parse_qs(urlparse(links.pop()).query)['token'][0]
        assert client.get('/api/auth/verify-email', params={'token': token}).status_code == 200
        login = client.post('/api/auth/login', json={
            'email': email, 'password': 'Strong-passphrase-123',
        })
        assert login.status_code == 200
        return client, uuid.UUID(login.json()['id'])

    yield create
    for client, email in reversed(accounts):
        client.close()
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                db.delete(user)
                db.commit()


@pytest.mark.parametrize('first', ['worker', 'employer'])
def test_second_like_creates_one_match(actors, first):
    employer, employer_id = actors('employer')
    worker, worker_id = actors('worker')
    outsider, _ = actors('employer')
    assert employer.put('/api/employers/me', json={
        'employer_type': 'business', 'display_name': 'Test Café',
    }).status_code == 200
    assert worker.put('/api/workers/me', json={
        'display_name': 'Test Worker', 'profession': 'Servicekraft',
    }).status_code == 200
    job_response = employer.post('/api/jobs', json={
        'category_id': 1, 'title': 'Servicekraft', 'city': 'Berlin', 'work_type': 'part_time',
    })
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()['id']
    requests = {
        'worker': (worker, {'job_id': job_id, 'action': 'like'}),
        'employer': (employer, {'job_id': job_id, 'worker_id': str(worker_id), 'action': 'like'}),
    }
    actor, data = requests[first]
    result = actor.post('/api/swipes', json=data)
    assert result.status_code == 201, result.text
    assert result.json()['is_match'] is False
    assert result.json()['match_id'] is None

    other = 'employer' if first == 'worker' else 'worker'
    actor, data = requests[other]
    result = actor.post('/api/swipes', json=data)
    assert result.status_code == 201, result.text
    assert result.json()['is_match'] is True
    match_id = result.json()['match_id']
    assert match_id

    for member in (worker, employer):
        listing = member.get('/api/matches')
        assert listing.status_code == 200
        assert any(item['id'] == match_id for item in listing.json())
        detail = member.get(f'/api/matches/{match_id}')
        assert detail.status_code == 200
        assert detail.json()['job_id'] == job_id
        assert detail.json()['worker_id'] == str(worker_id)

    assert outsider.get(f'/api/matches/{match_id}').status_code == 404
    assert not any(item['id'] == match_id for item in outsider.get('/api/matches').json())

    # An identical swipe is idempotent and does not produce another match.
    replay = actor.post('/api/swipes', json=data)
    assert replay.status_code == 201
    assert replay.json()['match_id'] == match_id
    with SessionLocal() as db:
        rows = db.scalars(select(Match).where(Match.job_id == uuid.UUID(job_id), Match.worker_id == worker_id)).all()
        assert len(rows) == 1


def test_pass_never_creates_match(actors):
    employer, _ = actors('employer')
    worker, worker_id = actors('worker')
    employer.put('/api/employers/me', json={'employer_type': 'private', 'display_name': 'Max'})
    worker.put('/api/workers/me', json={'display_name': 'Test painter'})
    job_id = employer.post('/api/jobs', json={
        'category_id': 5, 'title': 'Painter', 'city': 'Berlin', 'work_type': 'temporary',
    }).json()['id']
    assert worker.post('/api/swipes', json={'job_id': job_id, 'action': 'pass'}).status_code == 201
    response = employer.post('/api/swipes', json={
        'job_id': job_id, 'worker_id': str(worker_id), 'action': 'like',
    })
    assert response.status_code == 201
    assert response.json()['is_match'] is False
    assert worker.get('/api/matches').json() == []
