
"""Phase 6.1A regression checks. Run only against doppleja_v1_test."""
import uuid
from datetime import timedelta
from email import message_from_string
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User, VerificationToken
from backend.app.modules.auth import service


def test_mail_has_required_date_and_message_id(monkeypatch):
    messages=[]
    class FakeSMTP:
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def starttls(self, **kwargs): pass
        def login(self,*args): pass
        def send_message(self, message): messages.append(message)
    monkeypatch.setenv('AUTH_DEV_PRINT_LINK','false')
    monkeypatch.setenv('SMTP_HOST','mail.example.org')
    monkeypatch.setenv('SMTP_FROM','info@doppleja.de')
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.setattr(service.smtplib,'SMTP',FakeSMTP)
    service.send_verification_email('recipient@example.org','https://doppleja.de')
    assert len(messages)==1
    assert messages[0]['Date']
    assert messages[0]['Message-ID']


def test_resend_response_is_generic_and_existing_account_recovers(monkeypatch):
    email=f'resend-{uuid.uuid4().hex}@example.org'
    links=[]
    monkeypatch.setattr(service,'send_verification_email',lambda _,link: links.append(link))
    with TestClient(app) as client:
        registration=client.post('/api/auth/register',json={
            'email':email,'password':'Strong-passphrase-123','role':'worker'})
        assert registration.status_code==201, registration.text
        unknown=client.post('/api/auth/resend-verification',json={'email':f'absent-{uuid.uuid4().hex}@example.org'})
        existing=client.post('/api/auth/resend-verification',json={'email':email})
        assert unknown.status_code==existing.status_code==200
        assert unknown.json()==existing.json()
        # Initial token is only seconds old: cooldown means no extra email.
        assert len(links)==1
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email==email))
            token=db.scalar(select(VerificationToken).where(VerificationToken.user_id==user.id))
            token.created_at=service.utcnow()-timedelta(minutes=5)
            db.commit()
        again=client.post('/api/auth/resend-verification',json={'email':email})
        assert again.status_code==200
        assert len(links)==2
        original=parse_qs(urlparse(links[0]).query)['token'][0]
        newest=parse_qs(urlparse(links[1]).query)['token'][0]
        assert original != newest
        assert client.post('/api/auth/verify-email',data={'token':newest}).status_code==200
        assert client.post('/api/auth/resend-verification',json={'email':email}).status_code==200
        assert len(links)==2
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if user:
            db.delete(user)
            db.commit()


def test_smtp_failure_preserves_unverified_account_and_recovery(monkeypatch):
    email=f'smtpdown-{uuid.uuid4().hex}@example.org'
    def failure(*args): raise OSError('simulated outage')
    monkeypatch.setattr(service,'send_verification_email', failure)
    with TestClient(app) as client:
        reply=client.post('/api/auth/register',json={
            'email':email,'password':'Strong-passphrase-123','role':'employer'})
        assert reply.status_code==503
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email==email))
            assert user is not None and user.email_verified_at is None
            token=db.scalar(select(VerificationToken).where(VerificationToken.user_id==user.id))
            token.created_at=service.utcnow()-timedelta(minutes=5)
            db.commit()
        links=[]
        monkeypatch.setattr(service,'send_verification_email',lambda _,link: links.append(link))
        assert client.post('/api/auth/resend-verification',json={'email':email}).status_code==200
        assert len(links)==1
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if user:
            db.delete(user)
            db.commit()
