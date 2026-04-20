from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.checkpoint import Checkpoint, CheckpointStatusHistory
from app.repositories.checkpoint_repository import CheckpointRepository
from app.schemas.checkpoint import CheckpointCreate, CheckpointStatusCreate, CheckpointUpdate


class CheckpointService:
    @staticmethod
    def list_checkpoints(
        *,
        active_only: bool = False,
        governorate: str | None = None,
        page: int = 1,
        page_size: int = 50,
        order: str = "desc",
    ) -> list[Checkpoint]:
        with SessionLocal() as db:
            ids = CheckpointRepository.list_checkpoint_ids_paginated(
                db,
                active_only=active_only,
                governorate=governorate,
                page=page,
                page_size=page_size,
                order=order,
            )
            return CheckpointRepository.fetch_ordered(db, ids)

    @staticmethod
    def create_checkpoint(payload: CheckpointCreate) -> Checkpoint:
        with SessionLocal() as db:
            existing = CheckpointRepository.get_by_code(db, payload.code)
            if existing:
                raise ConflictException(message="Checkpoint code already exists")
            cp = Checkpoint(**payload.model_dump())
            return CheckpointRepository.add(db, cp)

    @staticmethod
    def get_checkpoint(checkpoint_id: int) -> Checkpoint:
        with SessionLocal() as db:
            cp = CheckpointRepository.get_by_id(db, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")
            return cp

    @staticmethod
    def update_checkpoint(checkpoint_id: int, payload: CheckpointUpdate) -> Checkpoint:
        with SessionLocal() as db:
            cp = CheckpointRepository.get_by_id(db, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")
            for k, v in payload.model_dump(exclude_none=True).items():
                setattr(cp, k, v)
            db.add(cp)
            db.commit()
            db.refresh(cp)
            return cp

    @staticmethod
    def add_status(checkpoint_id: int, payload: CheckpointStatusCreate, user_id: str) -> CheckpointStatusHistory:
        with SessionLocal() as db:
            cp = CheckpointRepository.get_by_id(db, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")

            current = CheckpointRepository.get_open_status(db, checkpoint_id)
            now = datetime.now(timezone.utc)
            if current:
                current.effective_to = now
                db.add(current)

            status = CheckpointStatusHistory(
                checkpoint_id=checkpoint_id,
                status=payload.status.upper(),
                reason=payload.reason,
                source_type="MODERATOR",
                effective_from=now,
                effective_to=None,
                created_by_user_id=str(user_id),
            )
            db.add(status)
            db.commit()
            db.refresh(status)
            return status

    @staticmethod
    def list_status_history(checkpoint_id: int) -> list[CheckpointStatusHistory]:
        with SessionLocal() as db:
            cp = CheckpointRepository.get_by_id(db, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")
            return CheckpointRepository.list_status_history(db, checkpoint_id)
