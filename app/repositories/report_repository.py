"""
Report persistence: ORM for writes/reads plus raw SQL for pagination and vote aggregation.

Raw SQL touchpoints (ORM + raw requirement):
- `list_report_ids_paginated` — windowed id list with sort (ported to repository)
- `find_recent_duplicate_candidates` — duplicate detection scan
- `vote_totals_for_report` — aggregation for credibility score
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.report import Report, ReportVote


QUEUE_STATUSES = ("PENDING", "UNDER_REVIEW")


class ReportRepository:
    @staticmethod
    def list_moderation_queue(db: Session) -> list[Report]:
        return list(
            db.execute(
                select(Report).where(Report.status.in_(QUEUE_STATUSES)).order_by(Report.created_at.desc())
            ).scalars().all()
        )

    @staticmethod
    def add(db: Session, report: Report) -> Report:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Report | None:
        return db.get(Report, report_id)

    @staticmethod
    def fetch_ordered(db: Session, ids: list[int]) -> list[Report]:
        if not ids:
            return []
        rows = list(db.execute(select(Report).where(Report.id.in_(ids))).scalars().all())
        by_id = {r.id: r for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    @staticmethod
    def list_report_ids_paginated(
        db: Session,
        *,
        status: str | None,
        user_id,
        category_id: int | None,
        page: int,
        page_size: int,
        sort_by: str,
        order: str,
    ) -> list[int]:
        allowed_sort_columns = {"created_at", "reported_at", "status", "credibility_score", "category_id"}
        sort_column = sort_by if sort_by in allowed_sort_columns else "created_at"
        sort_direction = "ASC" if order.lower() == "asc" else "DESC"
        clauses: list[str] = []
        params: dict = {"limit": page_size, "offset": max(page - 1, 0) * page_size}
        if status:
            clauses.append("status = :status")
            params["status"] = status
        if user_id is not None:
            clauses.append("user_id = :user_id")
            params["user_id"] = str(user_id)
        if category_id is not None:
            clauses.append("category_id = :category_id")
            params["category_id"] = category_id
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = text(
            f"""
            SELECT id
            FROM reports
            {where_sql}
            ORDER BY {sort_column} {sort_direction}
            LIMIT :limit OFFSET :offset
            """
        )
        rows = db.execute(sql, params).fetchall()
        return [int(row[0]) for row in rows]

    @staticmethod
    def find_recent_duplicate_candidates(
        db: Session,
        *,
        category_id: int,
        checkpoint_id: int | None,
        threshold: datetime,
    ) -> list[tuple[int, str | None]]:
        if checkpoint_id is None:
            sql = text(
                """
                SELECT id, description
                FROM reports
                WHERE category_id = :category_id
                  AND checkpoint_id IS NULL
                  AND reported_at >= :threshold
                ORDER BY reported_at DESC
                LIMIT 20
                """
            )
            params = {"category_id": category_id, "threshold": threshold}
        else:
            sql = text(
                """
                SELECT id, description
                FROM reports
                WHERE category_id = :category_id
                  AND checkpoint_id = :checkpoint_id
                  AND reported_at >= :threshold
                ORDER BY reported_at DESC
                LIMIT 20
                """
            )
            params = {"category_id": category_id, "checkpoint_id": checkpoint_id, "threshold": threshold}
        return [(int(rid), desc) for rid, desc in db.execute(sql, params).fetchall()]

    @staticmethod
    def get_vote(db: Session, report_id: int, user_id) -> ReportVote | None:
        return db.execute(
            select(ReportVote).where(ReportVote.report_id == report_id).where(ReportVote.user_id == user_id)
        ).scalar_one_or_none()

    @staticmethod
    def save_vote(db: Session, vote: ReportVote) -> None:
        db.add(vote)
        db.commit()

    @staticmethod
    def vote_totals_for_report(db: Session, report_id: int) -> tuple[int, int]:
        row = db.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN vote_value = 1 THEN 1 ELSE 0 END),0) AS upvotes,
                  COALESCE(SUM(CASE WHEN vote_value = -1 THEN 1 ELSE 0 END),0) AS downvotes
                FROM report_votes
                WHERE report_id = :report_id
                """
            ),
            {"report_id": report_id},
        ).fetchone()
        return int(row[0]), int(row[1])

    @staticmethod
    def refresh_report(db: Session, report: Report) -> Report:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
