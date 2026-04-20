from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlertSubscriptionCreate(BaseModel):
    area_name: str | None = Field(default=None, max_length=120)
    category_id: int | None = None
    min_severity: int = Field(default=1, ge=1, le=5)


class AlertSubscriptionRead(BaseModel):
    id: int
    user_id: UUID
    area_name: str | None
    category_id: int | None
    min_severity: int
    is_active: bool


class AlertRead(BaseModel):
    id: int
    incident_id: int
    category_id: int | None
    severity: int
    title: str
    body: str
    generated_at: datetime


class AlertDeliveryRead(AlertRead):
    delivery_status: str
    subscription_id: int
    read_at: datetime | None
