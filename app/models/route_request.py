from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RouteRequest(Base):
    __tablename__ = "route_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    origin_lat: Mapped[float] = mapped_column(nullable=False)
    origin_lng: Mapped[float] = mapped_column(nullable=False)
    destination_lat: Mapped[float] = mapped_column(nullable=False)
    destination_lng: Mapped[float] = mapped_column(nullable=False)
    transport_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    request_status: Mapped[str] = mapped_column(String(20), nullable=False)
    estimated_distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    factors_json: Mapped[str | None] = mapped_column(Text(), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
