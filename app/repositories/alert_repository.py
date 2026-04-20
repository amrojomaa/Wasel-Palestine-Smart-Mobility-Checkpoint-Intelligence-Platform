"""
Alert and subscription persistence: ORM reads/writes.

Raw SQL for alerts appears in incident-driven flows via `report_repository` / `incident_repository`;
subscription matching remains ORM for clarity and cross-dialect filters.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertDelivery, AlertSubscription
from app.models.incident import Incident


class AlertRepository:
    @staticmethod
    def list_subscriptions_for_user(db: Session, user_id) -> list[AlertSubscription]:
        return list(
            db.execute(
                select(AlertSubscription)
                .where(AlertSubscription.user_id == user_id)
                .order_by(AlertSubscription.id.desc())
            ).scalars().all()
        )

    @staticmethod
    def add_subscription(db: Session, sub: AlertSubscription) -> AlertSubscription:
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def get_subscription(db: Session, subscription_id: int) -> AlertSubscription | None:
        return db.get(AlertSubscription, subscription_id)

    @staticmethod
    def delete_subscription(db: Session, sub: AlertSubscription) -> None:
        db.delete(sub)
        db.commit()

    @staticmethod
    def get_incident(db: Session, incident_id: int) -> Incident | None:
        return db.get(Incident, incident_id)

    @staticmethod
    def add_alert(db: Session, alert: Alert) -> Alert:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def matching_subscriptions(db: Session, category_id: int | None, severity: int) -> list[AlertSubscription]:
        stmt = (
            select(AlertSubscription)
            .where(AlertSubscription.is_active.is_(True))
            .where((AlertSubscription.category_id.is_(None)) | (AlertSubscription.category_id == category_id))
            .where(AlertSubscription.min_severity <= severity)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def list_deliveries_join_alerts(
        db: Session,
        user_id,
        *,
        unread_only: bool,
        subscription_id: int | None,
    ) -> list[tuple[AlertDelivery, Alert]]:
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
        return list(db.execute(stmt).all())

    @staticmethod
    def get_delivery_for_user(db: Session, alert_id: int, user_id) -> AlertDelivery | None:
        return db.execute(
            select(AlertDelivery)
            .where(AlertDelivery.alert_id == alert_id)
            .where(AlertDelivery.user_id == user_id)
        ).scalar_one_or_none()
