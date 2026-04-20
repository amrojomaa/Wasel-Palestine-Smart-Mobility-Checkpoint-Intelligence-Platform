from datetime import datetime, timezone
from types import SimpleNamespace

from app.dependencies.auth import get_current_active_user


def test_moderation_action_and_promote(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.moderation_service import ModerationService

    monkeypatch.setattr(
        ModerationService,
        "act",
        lambda **kwargs: SimpleNamespace(
            id=1,
            report_id=kwargs["report_id"],
            action=kwargs["action"],
            to_status="APPROVED",
            created_at=datetime.now(timezone.utc),
        ),
    )
    monkeypatch.setattr(
        ModerationService,
        "promote_to_incident",
        lambda report_id, moderator_user_id: {"report_id": report_id, "incident_id": 55},
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        action_res = test_client.post(
            "/api/v1/moderation/reports/10/actions",
            json={"action": "APPROVE", "reason": "valid"},
            headers={"Authorization": "Bearer x"},
        )
        assert action_res.status_code == 200

        promote_res = test_client.post(
            "/api/v1/moderation/reports/10/promote-to-incident",
            headers={"Authorization": "Bearer x"},
        )
        assert promote_res.status_code == 200
        assert promote_res.json()["data"]["incident_id"] == 55
    finally:
        app.dependency_overrides.clear()
