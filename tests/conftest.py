"""Refuse destructive integration tests against development/production DBs."""
import os
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    name = os.environ.get('POSTGRES_DB', '')
    if not name.endswith('_test'):
        raise pytest.UsageError(
            'Integration tests require POSTGRES_DB ending in _test. '
            'Run with: docker compose exec -e POSTGRES_DB=doppleja_v1_test api python -m pytest tests/ -v'
        )


from backend.app.core import auth_protection


@pytest.fixture(autouse=True)
def isolate_auth_rate_limits(monkeypatch, request):
    """Isolate ordinary tests from shared Redis rate-limit counters."""
    if request.node.get_closest_marker("real_rate_limit"):
        return

    monkeypatch.setattr(
        auth_protection,
        "_throttle",
        lambda *args, **kwargs: True,
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_rate_limit: tests that exercise actual rate limiting",
    )
