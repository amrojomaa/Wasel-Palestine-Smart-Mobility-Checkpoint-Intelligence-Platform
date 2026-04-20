"""
Incident persistence: ORM for CRUD plus raw SQL for paginated listing (stable sort + limit/offset).

Raw SQL: `list_incident_ids_paginated`
ORM: loads `Incident` rows by id preserving list order.
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentVerificationEvent


class IncidentRepository:
    @staticmethod
    def list_incident_ids_paginated(
        db: Session,
        *,
        status: str | None,
        page: int,
        page_size: int,
        sort_by: str,
        order: str,
    ) -> list[int]:
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
        return [int(row[0]) for row in rows]

    @staticmethod
    def fetch_ordered(db: Session, ids: list[int]) -> list[Incident]:
        if not ids:
            return []
        rows = list(db.execute(select(Incident).where(Incident.id.in_(ids))).scalars().all())
        by_id = {r.id: r for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    @staticmethod
    def get_by_id(db: Session, incident_id: int) -> Incident | None:
        return db.get(Incident, incident_id)

    @staticmethod
    def add(db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def list_verification_events(db: Session, incident_id: int) -> list[IncidentVerificationEvent]:
        return list(
            db.execute(
                select(IncidentVerificationEvent)
                .where(IncidentVerificationEvent.incident_id == incident_id)
                .order_by(IncidentVerificationEvent.created_at.desc())
            ).scalars().all()
        )
