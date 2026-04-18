from datetime import datetime, timezone
from types import SimpleNamespace

from app.dependencies.auth import get_current_active_user


def test_incident_create_and_verify(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.incident_service import IncidentService

    monkeypatch.setattr(
        IncidentService,
        "create_incident",
        lambda payload, user_id, ip_address=None, user_agent=None: SimpleNamespace(
            id=1,
            category_id=payload.category_id,
            checkpoint_id=payload.checkpoint_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            status="OPEN",
            latitude=payload.latitude,
            longitude=payload.longitude,
            reported_at=datetime.now(timezone.utc),
            confidence_score=50.0,
        ),
    )

    monkeypatch.setattr(
        IncidentService,
        "verify_incident",
        lambda incident_id, action, reason, user_id, ip_address=None, user_agent=None: SimpleNamespace(
            id=101,
            incident_id=incident_id,
            action=action,
            previous_status="OPEN",
            new_status="VERIFIED",
            reason=reason,
            verifier_user_id=str(user_id),
            created_at=datetime.now(timezone.utc),
        ),
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        create_res = test_client.post(
            "/api/v1/incidents/",
            json={"category_id": 1, "title": "Delay", "severity": 3, "description": "Heavy delay"},
            headers={"Authorization": "Bearer x"},
        )
        assert create_res.status_code == 201

        verify_res = test_client.post(
            "/api/v1/incidents/1/verify",
            json={"action": "VERIFY", "reason": "confirmed"},
            headers={"Authorization": "Bearer x"},
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["data"]["new_status"] == "VERIFIED"
    finally:
        app.dependency_overrides.clear()


def test_incident_list_supports_sort_and_order(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.incident_service import IncidentService

    captured = {}

    def fake_list_incidents(status=None, page=1, page_size=20, sort_by="created_at", order="desc"):
        captured["status"] = status
        captured["page"] = page
        captured["page_size"] = page_size
        captured["sort_by"] = sort_by
        captured["order"] = order
        return []

    monkeypatch.setattr(IncidentService, "list_incidents", fake_list_incidents)

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        res = test_client.get(
            "/api/v1/incidents/?status=OPEN&page=2&page_size=10&sort_by=severity&order=asc",
            headers={"Authorization": "Bearer x"},
        )
        assert res.status_code == 200
        assert captured == {
            "status": "OPEN",
            "page": 2,
            "page_size": 10,
            "sort_by": "severity",
            "order": "asc",
        }
    finally:
        app.dependency_overrides.clear()
