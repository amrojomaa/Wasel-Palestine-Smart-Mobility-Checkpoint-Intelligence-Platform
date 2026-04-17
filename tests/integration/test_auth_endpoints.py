from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from app.dependencies.auth import get_current_active_user


def test_auth_login_with_service_mock(test_client, monkeypatch):
    from app.api.v1.endpoints import auth as auth_endpoint

    monkeypatch.setattr(
        auth_endpoint.AuthService,
        "login",
        lambda payload: auth_endpoint.TokenResponse(
            access_token="access.jwt",
            refresh_token="refresh.jwt",
            expires_in=900,
        ),
    )

    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass#123"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"] == "access.jwt"


def test_auth_me_with_dependency_override(test_client):
    from app.main import app

    def _fake_user():
        return SimpleNamespace(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="user@example.com",
            full_name="Test User",
            is_active=True,
            is_verified=True,
            roles=["citizen"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_current_active_user] = _fake_user
    try:
        response = test_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "user@example.com"
    finally:
        app.dependency_overrides.clear()
