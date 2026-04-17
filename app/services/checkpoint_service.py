from datetime import datetime, timezone

from sqlalchemy import select

from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import SessionLocal
from app.models.checkpoint import Checkpoint, CheckpointStatusHistory
from app.schemas.checkpoint import CheckpointCreate, CheckpointStatusCreate, CheckpointUpdate


class CheckpointService:
    @staticmethod
    def list_checkpoints() -> list[Checkpoint]:
        with SessionLocal() as db:
            return list(db.execute(select(Checkpoint).order_by(Checkpoint.id.desc())).scalars().all())

    @staticmethod
    def create_checkpoint(payload: CheckpointCreate) -> Checkpoint:
        with SessionLocal() as db:
            existing = db.execute(select(Checkpoint).where(Checkpoint.code == payload.code)).scalar_one_or_none()
            if existing:
                raise ConflictException(message="Checkpoint code already exists")
            cp = Checkpoint(**payload.model_dump())
            db.add(cp)
            db.commit()
            db.refresh(cp)
            return cp

    @staticmethod
    def get_checkpoint(checkpoint_id: int) -> Checkpoint:
        with SessionLocal() as db:
            cp = db.get(Checkpoint, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")
            return cp

    @staticmethod
    def update_checkpoint(checkpoint_id: int, payload: CheckpointUpdate) -> Checkpoint:
        with SessionLocal() as db:
            cp = db.get(Checkpoint, checkpoint_id)
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
            cp = db.get(Checkpoint, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")

            current = db.execute(
                select(CheckpointStatusHistory)
                .where(CheckpointStatusHistory.checkpoint_id == checkpoint_id)
                .where(CheckpointStatusHistory.effective_to.is_(None))
            ).scalar_one_or_none()
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
            cp = db.get(Checkpoint, checkpoint_id)
            if not cp:
                raise NotFoundException(message="Checkpoint not found")
            return list(
                db.execute(
                    select(CheckpointStatusHistory)
                    .where(CheckpointStatusHistory.checkpoint_id == checkpoint_id)
                    .order_by(CheckpointStatusHistory.effective_from.desc())
                ).scalars().all()
            )
