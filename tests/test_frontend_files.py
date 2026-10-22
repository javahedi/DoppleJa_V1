from pathlib import Path


def test_frontend_assets_present():
    root = Path(__file__).resolve().parents[1] / 'frontend'
    assert (root / 'index.html').is_file()
    assert (root / 'css/styles.css').is_file()
    assert (root / 'js/app.js').is_file()
    js = (root / 'js/app.js').read_text()
    assert '/api/auth/login' in js
    assert '/api/discovery/jobs' in js
    assert '/api/swipes' in js
    assert '/api/chats' in js
    assert '/ws/matches/' in js
