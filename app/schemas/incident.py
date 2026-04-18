from datetime import datetime

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    category_id: int
    checkpoint_id: int | None = None
    title: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    severity: int = Field(ge=1, le=5)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    occurred_at: datetime | None = None


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    severity: int | None = Field(default=None, ge=1, le=5)
    status: str | None = Field(default=None, min_length=2, max_length=30)


class IncidentRead(BaseModel):
    id: int
    category_id: int
    checkpoint_id: int | None
    title: str
    description: str | None
    severity: int
    status: str
    latitude: float | None
    longitude: float | None
    reported_at: datetime
    confidence_score: float


class IncidentVerifyRequest(BaseModel):
    action: str = Field(min_length=2, max_length=20)
    reason: str | None = Field(default=None, max_length=1000)


class IncidentVerificationRead(BaseModel):
    id: int
    incident_id: int
    action: str
    previous_status: str | None
    new_status: str
    reason: str | None
    verifier_user_id: str
    created_at: datetime
