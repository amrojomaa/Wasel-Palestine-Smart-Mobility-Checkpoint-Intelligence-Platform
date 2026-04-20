from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    category_id: int
    checkpoint_id: int | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    description: str = Field(min_length=10, max_length=2000)
    source_channel: str = Field(default="MOBILE", max_length=30)


class ReportRead(BaseModel):
    id: int
    user_id: UUID
    incident_id: int | None
    category_id: int
    checkpoint_id: int | None
    description: str
    status: str
    duplicate_of_report_id: int | None
    credibility_score: float
    reported_at: datetime


class ReportVoteRequest(BaseModel):
    vote_value: int = Field(ge=-1, le=1)


class ModerationActionRequest(BaseModel):
    action: str = Field(min_length=2, max_length=40)
    reason: str | None = Field(default=None, max_length=1000)
    duplicate_of_report_id: int | None = None
