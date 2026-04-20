from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.db.session import SessionLocal
from app.models.alert import Alert, AlertDelivery, AlertSubscription
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertDeliveryRead, AlertSubscriptionCreate
from app.services.audit_service import AuditService


class AlertService:
    @staticmethod
    def list_subscriptions(user_id) -> list[AlertSubscription]:
        with SessionLocal() as db:
            return AlertRepository.list_subscriptions_for_user(db, user_id)

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
            return AlertRepository.add_subscription(db, sub)

    @staticmethod
    def delete_subscription(user_id, subscription_id: int) -> None:
        with SessionLocal() as db:
            sub = AlertRepository.get_subscription(db, subscription_id)
            if not sub or sub.user_id != user_id:
                raise NotFoundException(message="Subscription not found")
            AlertRepository.delete_subscription(db, sub)

    @staticmethod
    def generate_for_verified_incident(incident_id: int, actor_user_id) -> dict:
        with SessionLocal() as db:
            incident = AlertRepository.get_incident(db, incident_id)
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
            alert = AlertRepository.add_alert(db, alert)

            subs = AlertRepository.matching_subscriptions(db, incident.category_id, incident.severity)

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
            rows = AlertRepository.list_deliveries_join_alerts(
                db,
                user_id,
                unread_only=unread_only,
                subscription_id=subscription_id,
            )
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
            delivery = AlertRepository.get_delivery_for_user(db, alert_id, user_id)
            if not delivery:
                raise NotFoundException(message="Alert delivery not found")
            if delivery.read_at is None:
                delivery.read_at = datetime.now(timezone.utc)
                delivery.delivery_status = "READ"
                db.add(delivery)
                db.commit()
            return {"alert_id": alert_id, "read": True, "read_at": delivery.read_at}
