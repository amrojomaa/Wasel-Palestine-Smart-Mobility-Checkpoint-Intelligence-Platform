import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

# Ensure test-safe settings before app imports.
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("AUTO_CREATE_TABLES", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("WEATHER_API_KEY", "dummy-weather-key")


@pytest.fixture()
def test_client():
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture()
def fake_current_user():
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        email="tester@wasel.local",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role_names=["admin", "moderator", "citizen"],
    )
