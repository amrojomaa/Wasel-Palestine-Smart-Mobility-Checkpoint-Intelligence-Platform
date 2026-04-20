"""
Checkpoint persistence: ORM for CRUD, listing, and status history.

Raw SQL: `checkpoint_counts_by_active_raw` — aggregate across the table (ORM + raw requirement).
List pagination uses SQLAlchemy Core (`select`) for portability across SQLite (tests) and PostgreSQL.
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.checkpoint import Checkpoint, CheckpointStatusHistory


class CheckpointRepository:
    @staticmethod
    def checkpoint_counts_by_active_raw(db: Session) -> tuple[int, int]:
        """Return (active_count, inactive_count) using portable raw SQL."""
        row = db.execute(
            text(
                """
                SELECT
                  SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active_n,
                  SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END) AS inactive_n
                FROM checkpoints
                """
            )
        ).fetchone()
        active_n = int(row[0] or 0)
        inactive_n = int(row[1] or 0)
        return active_n, inactive_n

    @staticmethod
    def list_checkpoint_ids_paginated(
        db: Session,
        *,
        active_only: bool,
        governorate: str | None,
        page: int,
        page_size: int,
        order: str,
    ) -> list[int]:
        stmt = select(Checkpoint.id)
        if active_only:
            stmt = stmt.where(Checkpoint.is_active.is_(True))
        if governorate is not None:
            stmt = stmt.where(Checkpoint.governorate == governorate)
        if order.lower() == "asc":
            stmt = stmt.order_by(Checkpoint.id.asc())
        else:
            stmt = stmt.order_by(Checkpoint.id.desc())
        stmt = stmt.limit(page_size).offset(max(page - 1, 0) * page_size)
        return [int(r[0]) for r in db.execute(stmt).all()]

    @staticmethod
    def fetch_ordered(db: Session, ids: list[int]) -> list[Checkpoint]:
        if not ids:
            return []
        rows = list(db.execute(select(Checkpoint).where(Checkpoint.id.in_(ids))).scalars().all())
        by_id = {r.id: r for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    @staticmethod
    def get_by_id(db: Session, checkpoint_id: int) -> Checkpoint | None:
        return db.get(Checkpoint, checkpoint_id)

    @staticmethod
    def get_by_code(db: Session, code: str) -> Checkpoint | None:
        return db.execute(select(Checkpoint).where(Checkpoint.code == code)).scalar_one_or_none()

    @staticmethod
    def add(db: Session, checkpoint: Checkpoint) -> Checkpoint:
        db.add(checkpoint)
        db.commit()
        db.refresh(checkpoint)
        return checkpoint

    @staticmethod
    def list_status_history(db: Session, checkpoint_id: int) -> list[CheckpointStatusHistory]:
        return list(
            db.execute(
                select(CheckpointStatusHistory)
                .where(CheckpointStatusHistory.checkpoint_id == checkpoint_id)
                .order_by(CheckpointStatusHistory.effective_from.desc())
            ).scalars().all()
        )

    @staticmethod
    def get_open_status(db: Session, checkpoint_id: int) -> CheckpointStatusHistory | None:
        return db.execute(
            select(CheckpointStatusHistory)
            .where(CheckpointStatusHistory.checkpoint_id == checkpoint_id)
            .where(CheckpointStatusHistory.effective_to.is_(None))
        ).scalar_one_or_none()

    @staticmethod
    def save(db: Session, *entities: object) -> None:
        for e in entities:
            db.add(e)
        db.commit()

    @staticmethod
    def refresh(db: Session, entity: object) -> None:
        db.refresh(entity)
