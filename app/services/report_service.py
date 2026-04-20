import hashlib
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.report import Report, ReportVote
from app.repositories.report_repository import ReportRepository
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
            return ReportRepository.add(db, report)

    @staticmethod
    def list_reports(
        status: str | None = None,
        user_id=None,
        *,
        category_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[Report]:
        with SessionLocal() as db:
            ids = ReportRepository.list_report_ids_paginated(
                db,
                status=status,
                user_id=user_id,
                category_id=category_id,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                order=order,
            )
            return ReportRepository.fetch_ordered(db, ids)

    @staticmethod
    def get_report(report_id: int) -> Report:
        with SessionLocal() as db:
            report = ReportRepository.get_by_id(db, report_id)
            if not report:
                raise NotFoundException(message="Report not found")
            return report

    @staticmethod
    def vote(report_id: int, user_id, vote_value: int) -> dict:
        if vote_value not in (-1, 1):
            raise ConflictException(message="vote_value must be -1 or 1")

        with SessionLocal() as db:
            report = ReportRepository.get_by_id(db, report_id)
            if not report:
                raise NotFoundException(message="Report not found")

            existing = ReportRepository.get_vote(db, report_id, user_id)

            now = datetime.now(timezone.utc)
            if existing:
                existing.vote_value = vote_value
                ReportRepository.save_vote(db, existing)
            else:
                ReportRepository.save_vote(
                    db,
                    ReportVote(report_id=report_id, user_id=user_id, vote_value=vote_value, created_at=now),
                )

            upvotes, downvotes = ReportRepository.vote_totals_for_report(db, report_id)
            score = max(0, min(100, 50 + (upvotes - downvotes) * 5))
            report.credibility_score = score
            ReportRepository.refresh_report(db, report)

            return {"upvotes": upvotes, "downvotes": downvotes, "credibility_score": float(score)}

    @staticmethod
    def _normalize_text(text_val: str) -> str:
        return " ".join(text_val.lower().split())

    @staticmethod
    def _find_recent_duplicate_id(db, category_id: int, checkpoint_id: int | None, duplicate_hash: str, normalized_description: str, now: datetime) -> int | None:
        threshold = now - timedelta(minutes=30)
        row = ReportRepository.find_recent_duplicate_candidates(
            db,
            category_id=category_id,
            checkpoint_id=checkpoint_id,
            threshold=threshold,
        )

        for rid, desc in row:
            existing_norm = ReportService._normalize_text(desc or "")
            if hashlib.sha256(f"{category_id}|{checkpoint_id}|{existing_norm[:120]}".encode("utf-8")).hexdigest() == duplicate_hash:
                return int(rid)
            if SequenceMatcher(a=existing_norm, b=normalized_description).ratio() >= 0.86:
                return int(rid)
        return None
