import json
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(
        action: str,
        entity_type: str,
        entity_id: str,
        actor_user_id=None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
        db=None,
    ) -> None:
        row = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=json.dumps(details or {}, default=str),
            created_at=datetime.now(timezone.utc),
        )

        if db is not None:
            db.add(row)
            return

        with SessionLocal() as session:
            session.add(row)
            session.commit()
