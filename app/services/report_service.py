import hashlib
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import select, text

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.report import Report, ReportVote
from app.schemas.report import ReportCreate


class ReportService:
    @staticmethod
    def create_report(payload: ReportCreate, user_id, ip_address: str | None = None) -> Report:
        with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            norm_description = ReportService._normalize_text(payload.description)
            duplicate_hash = hashlib.sha256(
                f"{payload.category_id}|{payload.checkpoint_id}|{norm_description[:120]}".encode("utf-8")
            ).hexdigest()

            duplicate_of = ReportService._find_recent_duplicate_id(
                db,
                category_id=payload.category_id,
                checkpoint_id=payload.checkpoint_id,
                duplicate_hash=duplicate_hash,
                normalized_description=norm_description,
                now=now,
            )

            report = Report(
                user_id=user_id,
                category_id=payload.category_id,
                checkpoint_id=payload.checkpoint_id,
                latitude=payload.latitude,
                longitude=payload.longitude,
                description=payload.description,
                source_channel=payload.source_channel,
                status="DUPLICATE" if duplicate_of else "PENDING",
                duplicate_of_report_id=duplicate_of,
                duplicate_hash=duplicate_hash,
                reported_at=now,
                abuse_score=0.00,
                credibility_score=50.00,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report

    @staticmethod
    def list_reports(status: str | None = None, user_id=None) -> list[Report]:
        with SessionLocal() as db:
            stmt = select(Report).order_by(Report.created_at.desc())
            if status:
                stmt = stmt.where(Report.status == status)
            if user_id:
                stmt = stmt.where(Report.user_id == user_id)
            return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_report(report_id: int) -> Report:
        with SessionLocal() as db:
            report = db.get(Report, report_id)
            if not report:
                raise NotFoundException(message="Report not found")
            return report

    @staticmethod
    def vote(report_id: int, user_id, vote_value: int) -> dict:
        if vote_value not in (-1, 1):
            raise ConflictException(message="vote_value must be -1 or 1")

        with SessionLocal() as db:
            report = db.get(Report, report_id)
            if not report:
                raise NotFoundException(message="Report not found")

            existing = db.execute(
                select(ReportVote).where(ReportVote.report_id == report_id).where(ReportVote.user_id == user_id)
            ).scalar_one_or_none()

            now = datetime.now(timezone.utc)
            if existing:
                existing.vote_value = vote_value
                db.add(existing)
            else:
                db.add(ReportVote(report_id=report_id, user_id=user_id, vote_value=vote_value, created_at=now))

            db.commit()

            totals = db.execute(
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
            upvotes, downvotes = int(totals[0]), int(totals[1])
            score = max(0, min(100, 50 + (upvotes - downvotes) * 5))
            report.credibility_score = score
            db.add(report)
            db.commit()

            return {"upvotes": upvotes, "downvotes": downvotes, "credibility_score": float(score)}

    @staticmethod
    def _normalize_text(text_val: str) -> str:
        return " ".join(text_val.lower().split())

    @staticmethod
    def _find_recent_duplicate_id(db, category_id: int, checkpoint_id: int | None, duplicate_hash: str, normalized_description: str, now: datetime) -> int | None:
        threshold = now - timedelta(minutes=30)
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

        row = db.execute(sql, params).fetchall()

        for rid, desc in row:
            existing_norm = ReportService._normalize_text(desc or "")
            if hashlib.sha256(f"{category_id}|{checkpoint_id}|{existing_norm[:120]}".encode("utf-8")).hexdigest() == duplicate_hash:
                return int(rid)
            if SequenceMatcher(a=existing_norm, b=normalized_description).ratio() >= 0.86:
                return int(rid)
        return None
