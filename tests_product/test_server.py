from fastapi.testclient import TestClient
from product.server import app, sessions
from product.core import Controller


def test_health_never_exposes_secrets_and_create_requires_configuration(monkeypatch):
    for key in ['RIME_API_KEY', 'LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']:
        monkeypatch.delenv(key, raising=False)
    client = TestClient(app)
    health = client.get('/api/health').json()
    assert health['configured'] is False
    assert 'RIME_API_KEY' in health['missing']
    assert client.post('/api/sessions', json={}).status_code == 503


def test_foreign_origin_and_form_submission_cannot_start_calls():
    client = TestClient(app)
    assert client.post('/api/sessions', json={}, headers={'Origin':'https://external.example'}).status_code == 403
    assert client.post('/api/sessions', data={}).status_code == 415
    assert client.get('/api/health', headers={'host':'external.example'}).status_code == 400


def test_session_access_requires_capability_and_no_text_confirmation_endpoint():
    class Worker:
        closed = False
        controller = Controller()
    sessions['example'] = {'secret':'secret', 'worker':Worker()}
    try:
        client = TestClient(app)
        assert client.get('/api/sessions/example').status_code == 404
        headers={'Authorization':'Bearer secret'}
        assert client.get('/api/sessions/example',headers=headers).status_code == 200
        assert client.post('/api/sessions/example/action',headers=headers,json={'action':'confirm'}).status_code == 422
        assert client.post('/api/sessions/example/action',headers=headers,json={'action':'start','text':'yes'}).status_code == 422
    finally:
        sessions.clear()


def test_failure_controls_disabled_by_default(monkeypatch):
    monkeypatch.setenv('DATAFORGE_TEST_MODE', '0')
    class Worker:
        closed = False
        controller = Controller()
    sessions['example'] = {'secret':'secret', 'worker':Worker()}
    try:
        client = TestClient(app)
        response=client.post('/api/sessions/example/action',headers={'Authorization':'Bearer secret'},json={'action':'speech_failure'})
        assert response.status_code == 403
    finally:
        sessions.clear()
