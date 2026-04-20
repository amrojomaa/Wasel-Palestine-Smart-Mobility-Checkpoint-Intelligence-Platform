from datetime import datetime, timezone
from types import SimpleNamespace

from app.dependencies.auth import get_current_active_user


def test_alert_subscription_and_read_flow(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.alert_service import AlertService

    monkeypatch.setattr(
        AlertService,
        "create_subscription",
        lambda user_id, payload: SimpleNamespace(
            id=1,
            user_id=user_id,
            area_name=payload.area_name,
            category_id=payload.category_id,
            min_severity=payload.min_severity,
            is_active=True,
        ),
    )
    monkeypatch.setattr(
        AlertService,
        "list_alerts",
        lambda user_id, unread_only=False, subscription_id=None: [
            {
                "id": 5,
                "incident_id": 12,
                "category_id": 1,
                "severity": 3,
                "title": "Verified incident",
                "body": "details",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "delivery_status": "SENT",
                "subscription_id": 1,
                "read_at": None,
            }
        ],
    )
    monkeypatch.setattr(
        AlertService,
        "mark_read",
        lambda alert_id, user_id: {"alert_id": alert_id, "read": True, "read_at": datetime.now(timezone.utc).isoformat()},
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        create_res = test_client.post(
            "/api/v1/alerts/subscriptions",
            json={"category_id": 1, "min_severity": 2},
            headers={"Authorization": "Bearer x"},
        )
        assert create_res.status_code == 201

        list_res = test_client.get(
            "/api/v1/alerts?unread_only=true",
            headers={"Authorization": "Bearer x"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) == 1

        mark_res = test_client.post(
            "/api/v1/alerts/5/mark-read",
            headers={"Authorization": "Bearer x"},
        )
        assert mark_res.status_code == 200
        assert mark_res.json()["data"]["read"] is True
    finally:
        app.dependency_overrides.clear()
