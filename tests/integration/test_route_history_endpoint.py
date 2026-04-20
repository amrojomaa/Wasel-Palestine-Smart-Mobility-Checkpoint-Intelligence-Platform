from datetime import datetime, timezone
from types import SimpleNamespace

from app.dependencies.auth import get_current_active_user


def test_route_history_endpoint(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.route_history_service import RouteHistoryService

    monkeypatch.setattr(
        RouteHistoryService,
        "list_for_user",
        lambda user_id: [
            SimpleNamespace(
                id=1,
                transport_mode="CAR",
                request_status="SUCCESS",
                estimated_distance_m=10000,
                estimated_duration_s=1200,
                requested_at=datetime.now(timezone.utc),
            )
        ],
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        response = test_client.get("/api/v1/routes/requests", headers={"Authorization": "Bearer x"})
        assert response.status_code == 200
        assert response.json()["data"][0]["request_status"] == "SUCCESS"
    finally:
        app.dependency_overrides.clear()
