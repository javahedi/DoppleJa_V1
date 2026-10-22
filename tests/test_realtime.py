"""Real-time messaging integration tests; requires isolated doppleja_v1_test DB."""
import pytest
from starlette.websockets import WebSocketDisconnect
from test_chat import setup_chat  # reuse Phase 4A's matched-user fixture


def test_worker_to_employer_and_reply(setup_chat):
    employer, worker, outsider, match_id, *_ = setup_chat
    path = f'/ws/matches/{match_id}'
    with worker.websocket_connect(path, headers={'origin': 'http://127.0.0.1:8001'}) as worker_ws:
        with employer.websocket_connect(path, headers={'origin': 'http://127.0.0.1:8001'}) as employer_ws:
            worker_ws.send_json({'type': 'message', 'content': 'Hallo WebSocket!'})
            a = worker_ws.receive_json()
            b = employer_ws.receive_json()
            assert a == b
            assert a['type'] == 'message'
            assert a['message']['content'] == 'Hallo WebSocket!'
            # Existing REST endpoint should notify open WebSockets, too.
            resp = employer.post(f'/api/matches/{match_id}/messages', json={'content': 'REST reply'})
            assert resp.status_code == 201
            assert worker_ws.receive_json()['message']['content'] == 'REST reply'
            assert employer_ws.receive_json()['message']['content'] == 'REST reply'
    history = worker.get(f'/api/matches/{match_id}/messages').json()
    assert [m['content'] for m in history] == ['Hallo WebSocket!', 'REST reply']


def test_outsider_cannot_connect(setup_chat):
    employer, worker, outsider, match_id, *_ = setup_chat
    with pytest.raises(WebSocketDisconnect):
        with outsider.websocket_connect(f'/ws/matches/{match_id}', headers={'origin': 'http://127.0.0.1:8001'}):
            pass


def test_bad_origin_and_invalid_message(setup_chat):
    employer, worker, outsider, match_id, *_ = setup_chat
    url = f'/ws/matches/{match_id}'
    with pytest.raises(WebSocketDisconnect):
        with worker.websocket_connect(url, headers={'origin': 'https://evil.example'}):
            pass
    with worker.websocket_connect(url, headers={'origin': 'http://127.0.0.1:8001'}) as ws:
        ws.send_json({'type': 'message', 'content': '   '})
        assert ws.receive_json()['type'] == 'error'
