"""Test both match states and participant-only access with the isolated test DB."""
from test_chat import setup_chat  # pytest fixture from the existing chat test module


def test_match_summaries_before_and_after_messages(setup_chat):
    employer, worker, outsider, match_id, job_id, *_ = setup_chat
    assert outsider.get('/api/match-summaries').json() == []
    for client, expected_name in ((worker, 'Test Café'), (employer, 'Test Worker')):
        response = client.get('/api/match-summaries')
        assert response.status_code == 200, response.text
        row = next(x for x in response.json() if x['match_id'] == match_id)
        assert row['job_title'] == 'Servicekraft'
        assert row['other_party_name'] == expected_name
        assert row['has_messages'] is False
        assert row['last_message'] is None
        assert row['matched_at']

    assert worker.post(f'/api/matches/{match_id}/messages', json={'content': 'Hallo Café'}).status_code == 201
    assert employer.post(f'/api/matches/{match_id}/messages', json={'content': 'Hallo zurück'}).status_code == 201
    for client in (worker, employer):
        row = next(x for x in client.get('/api/match-summaries').json() if x['match_id'] == match_id)
        assert row['has_messages'] is True
        assert row['last_message']['content'] == 'Hallo zurück'
        assert row['last_message']['created_at']
