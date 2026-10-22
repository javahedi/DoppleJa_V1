"""Worker likes history, dedicated test database only."""
from test_jobs import accounts

def test_pending_matched_unavailable_and_permissions(accounts):
    owner=accounts('employer')
    worker=accounts('worker')
    stranger=accounts('worker')
    assert owner.put('/api/employers/me',json={'employer_type':'business','display_name':'Test Café'}).status_code==200
    assert worker.put('/api/workers/me',json={'display_name':'Test Worker','profession':'Servicekraft'}).status_code==200
    assert stranger.put('/api/workers/me',json={'display_name':'Other Worker','profession':'Maler'}).status_code==200
    make=lambda title: owner.post('/api/jobs',json={'category_id':1,'title':title,'city':'Berlin','work_type':'part_time'})
    pending=make('Pending Job'); matched=make('Matched Job'); inactive=make('Inactive Job')
    for response in (pending,matched,inactive): assert response.status_code==201,response.text
    ids=[r.json()['id'] for r in (pending,matched,inactive)]
    for jid in ids: assert worker.post('/api/swipes',json={'job_id':jid,'action':'like'}).status_code==201
    first=worker.get('/api/workers/me/likes')
    assert first.status_code==200,first.text
    assert {row['job_id']:row['status'] for row in first.json()}=={jid:'pending' for jid in ids}
    assert stranger.get('/api/workers/me/likes').json()==[]
    assert owner.get('/api/workers/me/likes').status_code==403
    wid=worker.get('/api/auth/me').json()['id']
    assert owner.post('/api/swipes',json={'job_id':ids[1],'worker_id':wid,'action':'like'}).status_code==201
    assert owner.patch(f'/api/jobs/{ids[2]}/status',json={'action':'archive'}).status_code==200
    rows={row['job_id']:row for row in worker.get('/api/workers/me/likes').json()}
    assert rows[ids[0]]['status']=='pending'
    assert rows[ids[1]]['status']=='matched' and rows[ids[1]]['match_id']
    assert rows[ids[2]]['status']=='unavailable'
    assert len(worker.get('/api/workers/me/likes',params={'status':'matched'}).json())==1
    assert len(worker.get('/api/workers/me/likes',params={'status':'unavailable'}).json())==1
    assert worker.get('/api/workers/me/likes',params={'status':'invalid'}).status_code==422
    assert worker.post('/api/swipes',json={'job_id':ids[0],'action':'pass'}).status_code==409
