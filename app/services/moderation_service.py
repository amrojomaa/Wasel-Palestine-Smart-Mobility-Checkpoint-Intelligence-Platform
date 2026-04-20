from datetime import datetime, timezone

from sqlalchemy import select

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.report import Report, ReportModerationAction
from app.repositories.report_repository import ReportRepository
from app.services.audit_service import AuditService


class ModerationService:
    @staticmethod
    def queue() -> list[Report]:
        with SessionLocal() as db:
            return ReportRepository.list_moderation_queue(db)

    @staticmethod
    def act(report_id: int, action: str, reason: str | None, duplicate_of_report_id: int | None, moderator_user_id, ip_address: str | None = None, user_agent: str | None = None) -> ReportModerationAction:
        with SessionLocal() as db:
            report = db.get(Report, report_id)
            if not report:
                raise NotFoundException(message="Report not found")

            action_norm = action.upper()
            mapping = {
                "APPROVE": "APPROVED",
                "REJECT": "REJECTED",
                "MARK_DUPLICATE": "DUPLICATE",
                "MARK_SPAM": "SPAM",
                "REQUEST_INFO": "UNDER_REVIEW",
            }
            if action_norm not in mapping:
                raise ConflictException(message="Unsupported moderation action")
            if action_norm == "MARK_DUPLICATE" and not duplicate_of_report_id:
                raise ConflictException(message="duplicate_of_report_id is required for MARK_DUPLICATE")

            previous = report.status
            report.status = mapping[action_norm]
            report.duplicate_of_report_id = duplicate_of_report_id if action_norm == "MARK_DUPLICATE" else report.duplicate_of_report_id

            event = ReportModerationAction(
                report_id=report_id,
                moderator_user_id=moderator_user_id,
                action=action_norm,
                from_status=previous,
                to_status=report.status,
                reason=reason,
                duplicate_of_report_id=duplicate_of_report_id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(report)
            db.add(event)
            db.commit()
            db.refresh(event)

            AuditService.log(
                action=f"REPORT_{action_norm}",
                entity_type="REPORT",
                entity_id=str(report.id),
                actor_user_id=moderator_user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"from": previous, "to": report.status, "reason": reason},
                db=db,
            )
            db.commit()
            return event

    @staticmethod
    def promote_to_incident(report_id: int, moderator_user_id) -> dict:
        with SessionLocal() as db:
            report = db.get(Report, report_id)
            if not report:
                raise NotFoundException(message="Report not found")
            if report.status != "APPROVED":
                raise ConflictException(message="Only APPROVED reports can be promoted")
            if report.incident_id:
                raise ConflictException(message="Report already linked to an incident")

            incident = Incident(
                category_id=report.category_id,
                checkpoint_id=report.checkpoint_id,
                title="Incident created from citizen report",
                description=report.description,
                severity=3,
                status="OPEN",
                source_type="MODERATOR",
                latitude=report.latitude,
                longitude=report.longitude,
                occurred_at=report.reported_at,
                reported_at=datetime.now(timezone.utc),
                created_by_user_id=moderator_user_id,
                confidence_score=report.credibility_score,
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)

            report.incident_id = incident.id
            db.add(report)
            db.commit()
            return {"report_id": report.id, "incident_id": incident.id}
