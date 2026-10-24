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
def actors(monkeypatch):
    links=[]; accounts=[]
    monkeypatch.setattr(service, 'send_verification_email', lambda email, link: links.append(link))
    def create(role):
        email=f'swipe-{uuid.uuid4().hex}@example.org'
        client=TestClient(app)
        accounts.append((client,email))
        assert client.post('/api/auth/register',json={'email':email,'password':'Strong-passphrase-123','role':role}).status_code==201
        token=parse_qs(urlparse(links.pop()).query)['token'][0]
        assert client.post('/api/auth/verify-email',data={'token':token}).status_code==200
        login=client.post('/api/auth/login',json={'email':email,'password':'Strong-passphrase-123'})
        assert login.status_code==200
        return client, login.json()['id']
    yield create
    for client,email in accounts:
        client.close()
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email==email))
            if user:
                db.delete(user); db.commit()

def test_both_sides_swipe_and_no_repeats(actors):
    employer,eid=actors('employer'); worker,wid=actors('worker')
    assert employer.put('/api/employers/me',json={'employer_type':'business','display_name':'Nord Café'}).status_code==200
    assert worker.put('/api/workers/me',json={'display_name':'Sara Müller','profession':'Servicekraft'}).status_code==200
    job=employer.post('/api/jobs',json={'category_id':1,'title':'Servicekraft','city':'Berlin','work_type':'part_time'})
    assert job.status_code==201,job.text
    job_id=job.json()['id']
    assert any(x['id']==job_id for x in worker.get('/api/discovery/jobs').json())
    assert any(x['user_id']==wid for x in employer.get('/api/discovery/workers',params={'job_id':job_id}).json())
    data={'job_id':job_id,'action':'like'}
    assert worker.post('/api/swipes',json=data).status_code==201
    assert worker.post('/api/swipes',json=data).status_code==201
    assert worker.post('/api/swipes',json={**data,'action':'pass'}).status_code==409
    assert not any(x['id']==job_id for x in worker.get('/api/discovery/jobs').json())
    assert employer.post('/api/swipes',json={**data,'worker_id':wid}).status_code==201
    assert not any(x['user_id']==wid for x in employer.get('/api/discovery/workers',params={'job_id':job_id}).json())

def test_permissions_and_profile_required(actors):
    employer,eid=actors('employer'); worker,wid=actors('worker'); outsider,other=actors('employer')
    employer.put('/api/employers/me',json={'employer_type':'private','display_name':'Max'})
    job=employer.post('/api/jobs',json={'category_id':5,'title':'Painter','city':'Berlin','work_type':'temporary'})
    assert job.status_code==201
    job_id=job.json()['id']
    assert worker.post('/api/swipes',json={'job_id':job_id,'action':'like'}).status_code==400
    assert outsider.post('/api/swipes',json={'job_id':job_id,'worker_id':wid,'action':'like'}).status_code==403
    assert outsider.get('/api/discovery/workers',params={'job_id':job_id}).status_code==404
    assert worker.get('/api/discovery/workers',params={'job_id':job_id}).status_code==403
    assert employer.post('/api/swipes',json={'job_id':job_id,'action':'like'}).status_code==422
