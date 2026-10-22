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
def accounts(monkeypatch):
    links = []
    users = []
    monkeypatch.setattr(service, 'send_verification_email', lambda email, link: links.append(link))
    def create(role):
        email = f'job-test-{uuid.uuid4().hex}@example.org'
        client = TestClient(app)
        users.append((client,email))
        assert client.post('/api/auth/register',json={'email':email,'password':'Strong-passphrase-123','role':role}).status_code == 201
        token = parse_qs(urlparse(links.pop()).query)['token'][0]
        assert client.get('/api/auth/verify-email',params={'token':token}).status_code == 200
        assert client.post('/api/auth/login',json={'email':email,'password':'Strong-passphrase-123'}).status_code == 200
        return client
    yield create
    for client, email in users:
        client.close()
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user:
                db.delete(user)
                db.commit()

def test_employer_job_and_worker_discovery(accounts):
    employer = accounts('employer')
    worker = accounts('worker')
    assert employer.post('/api/jobs', json={'category_id':1,'title':'Servicekraft','city':'Berlin','work_type':'part_time'}).status_code == 400
    assert employer.put('/api/employers/me',json={'employer_type':'private','display_name':'Max Müller','city':'Berlin'}).status_code == 200
    categories = employer.get('/api/categories')
    assert categories.status_code == 200 and len(categories.json()) >= 7
    body = {'category_id':1,'title':'Servicekraft (m/w/d)','description':'Flexible Schichten','city':'Berlin','work_type':'part_time','hourly_pay_min':'15.00','hourly_pay_max':'18.00'}
    r = employer.post('/api/jobs',json=body)
    assert r.status_code == 201, r.text
    job_id = r.json()['id']
    assert len(employer.get('/api/jobs/mine').json()) == 1
    assert len(worker.get('/api/jobs/discover',params={'city':'Berlin'}).json()) == 1
    assert worker.get('/api/jobs/discover',params={'city':'Hamburg'}).json() == []
    assert worker.get('/api/jobs/discover',params={'category_id':2}).json() == []
    assert worker.get(f'/api/jobs/{job_id}').status_code == 200
    assert worker.put(f'/api/jobs/{job_id}',json=body).status_code == 403
    body['is_active'] = False
    assert employer.put(f'/api/jobs/{job_id}',json=body).status_code == 200
    discovery_response = worker.get("/api/jobs/discover")
    assert discovery_response.status_code == 200

    discovered_jobs = discovery_response.json()
    assert isinstance(discovered_jobs, list)
    assert worker.get(f'/api/jobs/{job_id}').status_code == 404
    assert employer.get(f'/api/jobs/{job_id}').status_code == 200

def test_jobs_reject_invalid_and_other_employer(accounts):
    a = accounts('employer')
    b = accounts('employer')
    w = accounts('worker')
    a.put('/api/employers/me',json={'employer_type':'business','display_name':'Nord Café'})
    b.put('/api/employers/me',json={'employer_type':'private','display_name':'Max'})
    body={'category_id':999,'title':'Painter','city':'Berlin','work_type':'temporary'}
    assert a.post('/api/jobs',json=body).status_code == 422
    body['category_id']=5
    body['hourly_pay_min']='20'
    body['hourly_pay_max']='10'
    assert a.post('/api/jobs',json=body).status_code == 422
    body['hourly_pay_max']='25'
    job=a.post('/api/jobs',json=body)
    assert job.status_code == 201,job.text
    assert b.put(f"/api/jobs/{job.json()['id']}",json=body).status_code == 404
    assert w.post('/api/jobs',json=body).status_code == 403
    assert a.get('/api/jobs/discover').status_code == 403
