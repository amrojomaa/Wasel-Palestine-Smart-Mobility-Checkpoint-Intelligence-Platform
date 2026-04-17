from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Checkpoint(Base, TimestampMixin):
    __tablename__ = "checkpoints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    governorate: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    status_history = relationship("CheckpointStatusHistory", back_populates="checkpoint", cascade="all, delete-orphan")


class CheckpointStatusHistory(Base):
    __tablename__ = "checkpoint_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checkpoint_id: Mapped[int] = mapped_column(ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="MODERATOR")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    checkpoint = relationship("Checkpoint", back_populates="status_history")
