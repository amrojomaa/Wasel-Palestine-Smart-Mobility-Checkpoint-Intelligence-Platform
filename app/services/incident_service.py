from datetime import datetime, timezone

from sqlalchemy import select, text

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.incident import Incident, IncidentVerificationEvent
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.audit_service import AuditService


class IncidentService:
    @staticmethod
    def list_incidents(
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[Incident]:
        with SessionLocal() as db:
            allowed_sort_columns = {"created_at", "reported_at", "severity", "status"}
            sort_column = sort_by if sort_by in allowed_sort_columns else "created_at"
            sort_direction = "ASC" if order.lower() == "asc" else "DESC"
            where_clause = "WHERE status = :status" if status else ""
            sql = text(
                f"""
                SELECT id
                FROM incidents
                {where_clause}
                ORDER BY {sort_column} {sort_direction}
                LIMIT :limit OFFSET :offset
                """
            )
            params = {"limit": page_size, "offset": max(page - 1, 0) * page_size}
            if status:
                params["status"] = status
            rows = db.execute(sql, params).fetchall()
            ids = [row[0] for row in rows]
            if not ids:
                return []
            return list(db.execute(select(Incident).where(Incident.id.in_(ids))).scalars().all())

    @staticmethod
    def create_incident(payload: IncidentCreate, user_id, ip_address: str | None = None, user_agent: str | None = None) -> Incident:
        with SessionLocal() as db:
            incident = Incident(
                **payload.model_dump(),
                status="OPEN",
                source_type="MODERATOR",
                reported_at=datetime.now(timezone.utc),
                created_by_user_id=user_id,
                confidence_score=50.00,
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)

            AuditService.log(
                action="INCIDENT_CREATED",
                entity_type="INCIDENT",
                entity_id=str(incident.id),
                actor_user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"status": incident.status, "severity": incident.severity},
                db=db,
            )
            db.commit()
            return incident

    @staticmethod
    def get_incident(incident_id: int) -> Incident:
        with SessionLocal() as db:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise NotFoundException(message="Incident not found")
            return incident

    @staticmethod
    def update_incident(incident_id: int, payload: IncidentUpdate) -> Incident:
        with SessionLocal() as db:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise NotFoundException(message="Incident not found")
            for k, v in payload.model_dump(exclude_none=True).items():
                setattr(incident, k, v)
            db.add(incident)
            db.commit()
            db.refresh(incident)
            return incident

    @staticmethod
    def verify_incident(incident_id: int, action: str, reason: str | None, user_id, ip_address: str | None = None, user_agent: str | None = None) -> IncidentVerificationEvent:
        with SessionLocal() as db:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise NotFoundException(message="Incident not found")

            prev = incident.status
            action_normalized = action.upper()
            mapping = {"VERIFY": "VERIFIED", "REJECT": "REJECTED", "REOPEN": "OPEN", "CLOSE": "CLOSED"}
            if action_normalized not in mapping:
                raise ConflictException(message="Invalid verification action")

            incident.status = mapping[action_normalized]
            now = datetime.now(timezone.utc)
            if action_normalized == "VERIFY":
                incident.verified_at = now
                incident.verified_by_user_id = user_id
            if action_normalized == "CLOSE":
                incident.closed_at = now
                incident.closed_by_user_id = user_id

            event = IncidentVerificationEvent(
                incident_id=incident_id,
                action=action_normalized,
                previous_status=prev,
                new_status=incident.status,
                reason=reason,
                verifier_user_id=user_id,
                created_at=now,
            )
            db.add(incident)
            db.add(event)
            db.commit()
            db.refresh(event)

            AuditService.log(
                action=f"INCIDENT_{action_normalized}",
                entity_type="INCIDENT",
                entity_id=str(incident.id),
                actor_user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"previous_status": prev, "new_status": incident.status, "reason": reason},
                db=db,
            )

            if action_normalized == "VERIFY":
                from app.services.alert_service import AlertService

                AlertService.generate_for_verified_incident(incident.id, actor_user_id=user_id)

            db.commit()
            return event

    @staticmethod
    def list_verification_events(incident_id: int) -> list[IncidentVerificationEvent]:
        with SessionLocal() as db:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise NotFoundException(message="Incident not found")
            return list(
                db.execute(
                    select(IncidentVerificationEvent)
                    .where(IncidentVerificationEvent.incident_id == incident_id)
                    .order_by(IncidentVerificationEvent.created_at.desc())
                ).scalars().all()
            )
