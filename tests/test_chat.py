"""Phase 4A integration tests; run only against doppleja_v1_test."""
import uuid
from urllib.parse import urlparse, parse_qs
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User, Message
from backend.app.modules.auth import service

@pytest.fixture
def setup_chat(monkeypatch):
    links = []
    users = []
    monkeypatch.setattr(service, 'send_verification_email', lambda email, link: links.append(link))

    def make_user(role):
        email = f'chat-{uuid.uuid4().hex}@example.org'
        client = TestClient(app)
        users.append((client, email))
        assert client.post('/api/auth/register', json={'email': email, 'password': 'Long-test-password-123', 'role': role}).status_code == 201
        token = parse_qs(urlparse(links.pop()).query)['token'][0]
        assert client.post('/api/auth/verify-email', data={'token': token}).status_code == 200
        response = client.post('/api/auth/login', json={'email': email, 'password': 'Long-test-password-123'})
        assert response.status_code == 200
        return client, response.json()['id']

    employer, employer_id = make_user('employer')
    worker, worker_id = make_user('worker')
    outsider, _ = make_user('employer')
    assert employer.put('/api/employers/me', json={'employer_type': 'business', 'display_name': 'Test Café'}).status_code == 200
    assert worker.put('/api/workers/me', json={'display_name': 'Test Worker', 'profession': 'Servicekraft'}).status_code == 200
    job = employer.post('/api/jobs', json={'category_id': 1, 'title': 'Servicekraft', 'city': 'Berlin', 'work_type': 'part_time'})
    assert job.status_code == 201, job.text
    job_id = job.json()['id']
    assert worker.post('/api/swipes', json={'job_id': job_id, 'action': 'like'}).status_code == 201
    liked = employer.post('/api/swipes', json={'job_id': job_id, 'worker_id': worker_id, 'action': 'like'})
    assert liked.status_code == 201, liked.text
    match_id = liked.json()['match_id']
    assert match_id
    yield employer, worker, outsider, match_id, job_id, worker_id, employer_id
    for client, email in reversed(users):
        client.close()
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user:
                db.delete(user)
                db.commit()


def test_chat_two_way_access_and_order(setup_chat):
    employer, worker, outsider, match_id, job_id, worker_id, employer_id = setup_chat
    route = f'/api/matches/{match_id}/messages'
    assert worker.get(route).json() == []
    assert employer.get(route).json() == []
    sent = worker.post(route, json={'content': '  Hallo!  '})
    assert sent.status_code == 201, sent.text
    assert sent.json()['content'] == 'Hallo!'
    assert sent.json()['sender_id'] == worker_id
    reply = employer.post(route, json={'content': 'Guten Tag!'} )
    assert reply.status_code == 201, reply.text
    assert reply.json()['sender_id'] == employer_id
    for client in (worker, employer):
        response = client.get(route)
        assert response.status_code == 200
        assert [m['content'] for m in response.json()] == ['Hallo!', 'Guten Tag!']
        chats = client.get('/api/chats')
        assert chats.status_code == 200
        our_chat = next(c for c in chats.json() if c['match_id'] == match_id)
        assert our_chat['job_id'] == job_id
        assert our_chat['last_message']['content'] == 'Guten Tag!'
        assert len(client.get(route, params={'limit': 1}).json()) == 1
        assert len(client.get(route, params={'limit': 1, 'offset': 1}).json()) == 1
    with SessionLocal() as db:
        assert len(db.scalars(select(Message).where(Message.match_id == uuid.UUID(match_id))).all()) == 2
    for method in ('get', 'post'):
        response = getattr(outsider, method)(route, **({'json': {'content': 'Hello'}} if method == 'post' else {}))
        assert response.status_code == 404
    assert not any(c['match_id'] == match_id for c in outsider.get('/api/chats').json())


def test_chat_reject_invalid_content_and_unknown_match(setup_chat):
    employer, worker, outsider, match_id, *_ = setup_chat
    url = f'/api/matches/{match_id}/messages'
    assert worker.post(url, json={'content': '  '}).status_code == 422
    assert worker.post(url, json={'content': 'x'*2001}).status_code == 422
    missing = f'/api/matches/{uuid.uuid4()}/messages'
    assert worker.post(missing, json={'content': 'Hello'}).status_code == 404
    assert worker.get(missing).status_code == 404
    assert worker.get(url, params={'limit': 101}).status_code == 422
    unauth = TestClient(app)
    assert unauth.get(url).status_code == 401
    assert unauth.post(url, json={'content': 'Hello'}).status_code == 401
    unauth.close()
