import pytest

from app.core.exceptions import RateLimitedException
from app.services.abuse_prevention_service import AbusePreventionService


def test_abuse_prevention_cooldown_triggered():
    AbusePreventionService._by_user.clear()
    AbusePreventionService._by_ip.clear()

    AbusePreventionService.check_report_submission("u1", "127.0.0.1")
    with pytest.raises(RateLimitedException):
        AbusePreventionService.check_report_submission("u1", "127.0.0.1")
