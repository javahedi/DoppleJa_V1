"""Phase 5.4: only matched parties confirm; reviews require two confirmations."""
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
def scenario(monkeypatch):
    links=[]; accounts=[]
    monkeypatch.setattr(service,'send_verification_email',lambda email,link: links.append(link))
    def make(role):
        email=f'reviews-{uuid.uuid4().hex}@example.org'
        client=TestClient(app);accounts.append((client,email))
        assert client.post('/api/auth/register',json={'email':email,'password':'Long-test-password-123','role':role}).status_code==201
        token=parse_qs(urlparse(links.pop()).query)['token'][0]
        assert client.get('/api/auth/verify-email',params={'token':token}).status_code==200
        result=client.post('/api/auth/login',json={'email':email,'password':'Long-test-password-123'})
        assert result.status_code==200
        return client,result.json()['id']
    employer,eid=make('employer');worker,wid=make('worker');outsider,_=make('worker')
    assert employer.put('/api/employers/me',json={'employer_type':'business','display_name':'Review Café'}).status_code==200
    assert worker.put('/api/workers/me',json={'display_name':'Review Worker','profession':'Servicekraft'}).status_code==200
    job=employer.post('/api/jobs',json={'category_id':1,'title':'Servicekraft','city':'Berlin','work_type':'part_time'})
    assert job.status_code==201,job.text
    jid=job.json()['id']
    assert worker.post('/api/swipes',json={'job_id':jid,'action':'like'}).status_code==201
    matched=employer.post('/api/swipes',json={'job_id':jid,'worker_id':wid,'action':'like'})
    assert matched.status_code==201,matched.text
    mid=matched.json()['match_id']
    yield employer,worker,outsider,mid,eid,wid
    for client,email in reversed(accounts):
        client.close()
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email==email))
            if user:db.delete(user);db.commit()

def test_completion_and_two_way_stars(scenario):
    employer,worker,outsider,mid,eid,wid=scenario
    url=f'/api/matches/{mid}'
    assert outsider.get(url+'/completion').status_code==404
    assert outsider.post(url+'/confirm-completion').status_code==404
    assert worker.get(url+'/completion').json()['completed'] is False
    assert worker.post(url+'/reviews',json={'stars':5}).status_code==409
    once=worker.post(url+'/confirm-completion')
    assert once.status_code==200 and once.json()['confirmed_by_me'] is True
    assert once.json()['completed'] is False
    assert worker.post(url+'/confirm-completion').status_code==200
    assert employer.post(url+'/confirm-completion').json()['completed'] is True
    assert worker.post(url+'/reviews',json={'stars':0}).status_code==422
    assert worker.post(url+'/reviews',json={'stars':6}).status_code==422
    assert worker.post(url+'/reviews',json={'stars':5,'comment':'Great employer'}).status_code==201
    assert worker.post(url+'/reviews',json={'stars':4}).status_code==409
    assert employer.post(url+'/reviews',json={'stars':4,'comment':'Reliable worker'}).status_code==201
    assert worker.get(url+'/completion').json()['their_review']['stars']==4
    assert employer.get(url+'/completion').json()['their_review']['stars']==5
    assert worker.get(f'/api/users/{wid}/rating').json()['average']==4.0
    assert employer.get(f'/api/users/{eid}/rating').json()['average']==5.0
    assert outsider.post(url+'/reviews',json={'stars':5}).status_code==404
    # Public reputation comes only from reviews received, not those authored.
    employer_public=worker.get(f'/api/users/{eid}/rating')
    assert employer_public.status_code==200
    assert employer_public.json()['average']==5.0
    assert employer_public.json()['count']==1
    worker_public=employer.get(f'/api/users/{wid}/rating')
    assert worker_public.json()['average']==4.0
    assert worker_public.json()['count']==1
    employer_received=worker.get(f'/api/users/{eid}/reviews')
    assert employer_received.status_code==200
    assert len(employer_received.json())==1
    assert employer_received.json()[0]['stars']==5
    assert employer_received.json()[0]['reviewee_id']==eid
    worker_received=employer.get(f'/api/users/{wid}/reviews')
    assert len(worker_received.json())==1
    assert worker_received.json()[0]['stars']==4
    assert worker_received.json()[0]['reviewee_id']==wid
    assert worker.get(f'/api/users/{wid}/reviews?limit=51').status_code==422
    assert worker.get('/api/users/00000000-0000-0000-0000-000000000001/reviews').status_code==404
