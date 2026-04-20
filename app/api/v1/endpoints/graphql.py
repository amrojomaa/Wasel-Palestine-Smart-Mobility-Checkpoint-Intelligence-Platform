import strawberry
from sqlalchemy import func, select
from strawberry.fastapi import GraphQLRouter

from app.db.session import SessionLocal
from app.models.checkpoint import Checkpoint
from app.models.incident import Incident
from app.models.report import Report


@strawberry.type
class SystemStats:
    checkpoints: int
    incidents: int
    reports: int


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    def system_stats(self) -> SystemStats:
        with SessionLocal() as db:
            checkpoints = db.execute(select(func.count()).select_from(Checkpoint)).scalar_one()
            incidents = db.execute(select(func.count()).select_from(Incident)).scalar_one()
            reports = db.execute(select(func.count()).select_from(Report)).scalar_one()

        return SystemStats(
            checkpoints=int(checkpoints),
            incidents=int(incidents),
            reports=int(reports),
        )

    @strawberry.field
    def recent_incident_titles(self, limit: int = 5) -> list[str]:
        safe_limit = max(1, min(limit, 20))
        with SessionLocal() as db:
            rows = db.execute(select(Incident.title).order_by(Incident.reported_at.desc()).limit(safe_limit)).all()
        return [row[0] for row in rows]


schema = strawberry.Schema(query=Query)
router = GraphQLRouter(schema)
