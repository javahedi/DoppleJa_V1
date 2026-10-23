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
