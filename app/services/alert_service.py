from datetime import datetime, timezone

from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.db.session import SessionLocal
from app.models.alert import Alert, AlertDelivery, AlertSubscription
from app.models.incident import Incident
from app.schemas.alert import AlertDeliveryRead, AlertSubscriptionCreate
from app.services.audit_service import AuditService


class AlertService:
    @staticmethod
    def list_subscriptions(user_id) -> list[AlertSubscription]:
        with SessionLocal() as db:
            return list(
                db.execute(
                    select(AlertSubscription)
                    .where(AlertSubscription.user_id == user_id)
                    .order_by(AlertSubscription.id.desc())
                ).scalars().all()
            )

    @staticmethod
    def create_subscription(user_id, payload: AlertSubscriptionCreate) -> AlertSubscription:
        with SessionLocal() as db:
            sub = AlertSubscription(
                user_id=user_id,
                area_name=payload.area_name,
                category_id=payload.category_id,
                min_severity=payload.min_severity,
                is_active=True,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
            return sub

    @staticmethod
    def delete_subscription(user_id, subscription_id: int) -> None:
        with SessionLocal() as db:
            sub = db.get(AlertSubscription, subscription_id)
            if not sub or sub.user_id != user_id:
                raise NotFoundException(message="Subscription not found")
            db.delete(sub)
            db.commit()

    @staticmethod
    def generate_for_verified_incident(incident_id: int, actor_user_id) -> dict:
        with SessionLocal() as db:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise NotFoundException(message="Incident not found")

            alert = Alert(
                incident_id=incident.id,
                category_id=incident.category_id,
                severity=incident.severity,
                title=f"Verified incident: {incident.title}",
                body=incident.description or "A verified incident was reported.",
                generated_at=datetime.now(timezone.utc),
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

            subs = list(
                db.execute(
                    select(AlertSubscription)
                    .where(AlertSubscription.is_active.is_(True))
                    .where((AlertSubscription.category_id.is_(None)) | (AlertSubscription.category_id == incident.category_id))
                    .where(AlertSubscription.min_severity <= incident.severity)
                ).scalars().all()
            )

            now = datetime.now(timezone.utc)
            delivered = 0
            for sub in subs:
                db.add(
                    AlertDelivery(
                        alert_id=alert.id,
                        subscription_id=sub.id,
                        user_id=sub.user_id,
                        delivery_status="SENT",
                        delivered_at=now,
                        read_at=None,
                    )
                )
                delivered += 1

            AuditService.log(
                action="ALERT_GENERATED",
                entity_type="ALERT",
                entity_id=str(alert.id),
                actor_user_id=actor_user_id,
                details={"incident_id": incident.id, "deliveries": delivered},
                db=db,
            )
            db.commit()
            return {"alert_id": alert.id, "deliveries": delivered}

    @staticmethod
    def list_alerts(user_id, unread_only: bool = False, subscription_id: int | None = None) -> list[AlertDeliveryRead]:
        with SessionLocal() as db:
            stmt = (
                select(AlertDelivery, Alert)
                .join(Alert, Alert.id == AlertDelivery.alert_id)
                .where(AlertDelivery.user_id == user_id)
                .order_by(Alert.generated_at.desc())
            )
            if unread_only:
                stmt = stmt.where(AlertDelivery.read_at.is_(None))
            if subscription_id is not None:
                stmt = stmt.where(AlertDelivery.subscription_id == subscription_id)

            rows = db.execute(stmt).all()
            return [
                AlertDeliveryRead(
                    id=alert.id,
                    incident_id=alert.incident_id,
                    category_id=alert.category_id,
                    severity=alert.severity,
                    title=alert.title,
                    body=alert.body,
                    generated_at=alert.generated_at,
                    delivery_status=delivery.delivery_status,
                    subscription_id=delivery.subscription_id,
                    read_at=delivery.read_at,
                )
                for delivery, alert in rows
            ]

    @staticmethod
    def mark_read(alert_id: int, user_id) -> dict:
        with SessionLocal() as db:
            delivery = db.execute(
                select(AlertDelivery)
                .where(AlertDelivery.alert_id == alert_id)
                .where(AlertDelivery.user_id == user_id)
            ).scalar_one_or_none()
            if not delivery:
                raise NotFoundException(message="Alert delivery not found")
            if delivery.read_at is None:
                delivery.read_at = datetime.now(timezone.utc)
                delivery.delivery_status = "READ"
                db.add(delivery)
                db.commit()
            return {"alert_id": alert_id, "read": True, "read_at": delivery.read_at}
