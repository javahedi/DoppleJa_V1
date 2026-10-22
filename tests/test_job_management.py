"""Phase 5.1A owner-only job lifecycle tests, run against dedicated test DB."""
from test_jobs import accounts


def test_pause_reactivate_edit_archive(accounts):
    owner = accounts('employer')
    other = accounts('employer')
    worker = accounts('worker')
    owner.put('/api/employers/me', json={'employer_type': 'private', 'display_name': 'Max Müller'})
    other.put('/api/employers/me', json={'employer_type': 'business', 'display_name': 'Anderes Café'})
    body = {'category_id': 4, 'title': 'Maler', 'city': 'Bremen', 'work_type': 'temporary'}
    result = owner.post('/api/jobs', json=body)
    assert result.status_code == 201, result.text
    job_id = result.json()['id']
    path = f'/api/jobs/{job_id}/status'
    assert other.patch(path, json={'action': 'pause'}).status_code == 404
    assert worker.patch(path, json={'action': 'pause'}).status_code == 403
    assert owner.patch(path, json={'action': 'pause'}).json()['is_active'] is False
    edited = {**body, 'title': 'Maler & Lackierer', 'is_active': False}
    updated = owner.put(f'/api/jobs/{job_id}', json=edited)
    assert updated.status_code == 200, updated.text
    assert updated.json()['title'] == 'Maler & Lackierer'
    assert owner.patch(path, json={'action': 'reactivate'}).json()['is_active'] is True
    archived = owner.patch(path, json={'action': 'archive'})
    assert archived.status_code == 200
    assert archived.json()['archived_at'] is not None
    assert archived.json()['is_active'] is False
    assert owner.get('/api/jobs/mine').json()[0]['archived_at'] is not None
    assert owner.get(f'/api/jobs/{job_id}').status_code == 200
    assert worker.get(f'/api/jobs/{job_id}').status_code == 404
    assert owner.patch(path, json={'action': 'reactivate'}).status_code == 409
    assert owner.put(f'/api/jobs/{job_id}', json=body).status_code == 409
    assert all(item['id'] != job_id for item in worker.get('/api/discovery/jobs').json())
    assert all(item['id'] != job_id for item in worker.get('/api/jobs/discover').json())


def test_only_known_actions(accounts):
    employer = accounts('employer')
    assert employer.patch('/api/jobs/00000000-0000-0000-0000-000000000001/status', json={'action': 'delete'}).status_code == 422
