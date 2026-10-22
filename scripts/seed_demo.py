"""DoppleJa isolated development-demo seeder. Run inside the API container.
Only connects when BOTH POSTGRES_DB and current_database() equal doppleja_v1_demo.
"""
from __future__ import annotations
import os, random, uuid, sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import text
from backend.app.core.database import get_db
from backend.app.models import User, WorkerProfile, EmployerProfile, Job, JobCategory, Swipe, Match, Message
from backend.app.modules.auth.security import hash_password

DB_NAME = 'doppleja_v1_demo'
NAMESPACE = uuid.UUID('8930bf95-0c57-483a-97f4-4e720f82653c')
def uid(kind, number): return uuid.uuid5(NAMESPACE, f'{kind}:{number}')
rng = random.Random(52024)
CITIES = ['Berlin','Düsseldorf','Bremen','Hamburg','Köln','München','Frankfurt am Main','Leipzig','Dortmund','Essen','Stuttgart','Hannover']
FIRST = ['Sara','Mina','Lena','Fatima','Sophie','Ali','Amir','Ben','Jonas','Nina','Maya','Lea','Daniel','Mohammad','Elif','Paul','Emma','Yusuf','Max','Laura']
LAST = ['Müller','Schneider','Weber','Kaya','Becker','Hoffmann','Wagner','Fischer','Demir','Schulz','Schmidt','Neumann','Öztürk','Braun','Yilmaz']
WORK = [
    (1,'Servicekraft','Servicekraft (m/w/d)', 'Gastronomie'),
    (1,'Barista','Barista (m/w/d)', 'Gastronomie'),
    (2,'Pflegehelfer','Pflegehilfe (m/w/d)', 'Pflege'),
    (3,'Fahrer','Auslieferungsfahrer (m/w/d)', 'Logistik'),
    (4,'Elektriker','Elektromontage (m/w/d)', 'Handwerk'),
    (4,'Tischler','Werkstatthelfer (m/w/d)', 'Handwerk'),
    (5,'Maler','Malerhelfer (m/w/d)', 'Bau'),
    (6,'Reinigungskraft','Reinigungskraft (m/w/d)', 'Reinigung'),
    (7,'Eventhelfer','Event-Aufbauhilfe (m/w/d)', 'Events'),
    (8,'Verkäuferin','Verkaufshilfe (m/w/d)', 'Einzelhandel'),
]
BUSINESS = ['Nord Café','Luna Restaurant','Hafen Logistik','Handwerk Plus','Stadtblick Reinigung','Kiez Bäckerei','Lebensfreude Pflege','Rhein Events','Markt & Mehr','Grünwerk Service','Morgenstern Bistro','Klar & Sauber']
ASSET_BASE='/app-assets/assets/dj-people/'
WORKER_PHOTOS=['candidate-service.webp','candidate-care.webp','candidate-craft.webp','job-painting.webp','job-logistics.webp','job-cleaning.webp']
EMPLOYER_PHOTOS=['employer-cafe.webp','employer-care.webp','employer-craft.webp']


def upsert(session, model, key, **fields):
    obj=session.get(model,key)
    if obj is None:
        obj=model(**{next(iter(model.__mapper__.primary_key)).name:key}, **fields)
        session.add(obj)
    return obj


def main():
    if os.environ.get('POSTGRES_DB') != DB_NAME:
        raise SystemExit(f'REFUSED: POSTGRES_DB must be {DB_NAME}, not {os.environ.get("POSTGRES_DB")!r}')
    generator=get_db()
    session=next(generator)
    try:
        actual=session.execute(text('select current_database()')).scalar_one()
        if actual != DB_NAME: raise SystemExit(f'REFUSED: actual database is {actual!r}')
        # Never populate a database with accounts outside the clearly marked demo domain.
        if session.execute(text("select count(*) from users where email not like '%@example.com'")).scalar_one():
            raise SystemExit('REFUSED: database includes non-demo users')
        available=set(session.execute(text('select id from job_categories')).scalars())
        needed={t[0] for t in WORK}
        if not needed.issubset(available): raise SystemExit('Missing job categories. Run Alembic migrations first.')
        password=hash_password('Demo2026!')
        employers=[]; workers=[]; jobs=[]
        for i in range(1,51):
            user_id=uid('employer',i)
            email=f'employer{i:02d}@example.com'
            upsert(session, User, user_id, email=email, password_hash=password,
                   role='employer',is_active=True,email_verified_at=datetime.now(timezone.utc))
            session.flush()
            private=i%5==0
            label=(f'{FIRST[(i+5)%len(FIRST)]} {LAST[i%len(LAST)]}' if private else
                   f'{BUSINESS[(i-1)%len(BUSINESS)]} {i:02d}')
            city=CITIES[(i-1)%len(CITIES)]
            photo=(None if i%3==0 else ASSET_BASE+EMPLOYER_PHOTOS[i%len(EMPLOYER_PHOTOS)])
            upsert(session, EmployerProfile, user_id, employer_type='private' if private else 'business',
                   display_name=label,city=city,category='Privater Auftrag' if private else WORK[i%len(WORK)][3],
                   description='DEMO-PROFIL – Beispiel für Design- und Funktionstests.', photo_url=photo)
            employers.append((user_id,city,label))
        for i in range(1,101):
            user_id=uid('worker',i); category,profession,_,_=WORK[(i-1)%len(WORK)]
            upsert(session, User,user_id,email=f'worker{i:03d}@example.com', password_hash=password,
                   role='worker',is_active=True,email_verified_at=datetime.now(timezone.utc))
            session.flush()
            upsert(session,WorkerProfile,user_id,display_name=f'{FIRST[(i-1)%len(FIRST)]} {LAST[(i*3)%len(LAST)]}',
                   profession=profession,city=CITIES[(i-1)%len(CITIES)],
                   availability=['Ab sofort','In 1–2 Wochen','Flexibel'][i%3],
                   bio='DEMO-PROFIL – Freundlich, zuverlässig und motiviert. Dies ist keine echte arbeitssuchende Person.',
                   photo_url=ASSET_BASE+WORKER_PHOTOS[(i-1)%len(WORKER_PHOTOS)])
            workers.append(user_id)
        # At least 1 job per employer: 50 employers + 50 additional jobs = 100.
        for j in range(1,101):
            employer_idx=(j-1)%50; employer_id,city,_=employers[employer_idx]
            category,_,title,_=WORK[(j-1)%len(WORK)]
            job_id=uid('job',j)
            created=datetime.now(timezone.utc)-timedelta(days=(j*7)%45,hours=j%18)
            archived=(j%20==0)
            upsert(session,Job,job_id,employer_id=employer_id,category_id=category,title=title,
                   description='DEMO-STELLENANZEIGE – Nur für Entwicklungs- und UI-Tests. Flexible Aufgaben und freundliches Team.',
                   city=city,work_type=['part_time','minijob','full_time','temporary'][j%4],
                   hourly_pay_min=Decimal(14+(j%7)),hourly_pay_max=Decimal(16+(j%7)+(j%4)),
                   is_active=(j%12!=0 and not archived), created_at=created)
            jobs.append((job_id,employer_id))
        session.flush()
        # 25 matched pairs (50 likes), 18 conversations, 10 pending likes, 10 passed jobs.
        for k in range(1,26):
            job_id,employer_id=jobs[(k*3-1)%len(jobs)]
            worker_id=workers[(k*5-1)%len(workers)]
            for role in ('worker','employer'):
                upsert(session,Swipe,uid(f'swipe-{role}',k),job_id=job_id,worker_id=worker_id,
                       actor_role=role,action='like')
            match_id=uid('match',k)
            upsert(session,Match,match_id,job_id=job_id,worker_id=worker_id)
            if k<=18:
                for n in range(1,4):
                    sender=worker_id if n%2==0 else employer_id
                    content=(['Hallo! Ist die Stelle noch verfügbar?',
                              'Hallo! Ja, wir suchen noch Unterstützung.',
                              'Super, wann können wir kurz sprechen?'][n-1])
                    upsert(session,Message,uid(f'message-{k}',n),match_id=match_id,sender_id=sender,content=content)
        for k in range(26,36):
            job_id,_=jobs[(k*2)%len(jobs)]; worker_id=workers[(k*7)%len(workers)]
            upsert(session,Swipe,uid('pending',k),job_id=job_id,worker_id=worker_id,actor_role='worker',action='like')
        for k in range(36,46):
            job_id,_=jobs[(k*2)%len(jobs)]; worker_id=workers[(k*7)%len(workers)]
            upsert(session,Swipe,uid('passed',k),job_id=job_id,worker_id=worker_id,actor_role='worker',action='pass')
        session.commit()
        print('SUCCESS: isolated demo database seeded — 50 employers, 100 workers, 100 jobs, 25 matches, 54 messages.')
        print('Accounts: worker001@example.com / Demo2026!')
        print('          employer01@example.com / Demo2026!')
        print('All generated accounts are email-verified. All content is DEMO/illustrative.')
    except:
        session.rollback(); raise
    finally:
        generator.close()

if __name__ == '__main__': main()
