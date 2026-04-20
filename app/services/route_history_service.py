import json
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.route_request import RouteRequest
from app.schemas.routing import RouteEstimateRequest


class RouteHistoryService:
    @staticmethod
    def store(user_id, payload: RouteEstimateRequest, result: dict) -> RouteRequest:
        with SessionLocal() as db:
            row = RouteRequest(
                user_id=user_id,
                origin_lat=payload.origin.lat,
                origin_lng=payload.origin.lng,
                destination_lat=payload.destination.lat,
                destination_lng=payload.destination.lng,
                transport_mode=payload.transport_mode,
                request_status="SUCCESS",
                estimated_distance_m=result.get("estimated_distance_m"),
                estimated_duration_s=result.get("estimated_duration_s"),
                factors_json=json.dumps(result.get("factors", {}), default=str),
                requested_at=datetime.now(timezone.utc),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    @staticmethod
    def list_for_user(user_id) -> list[RouteRequest]:
        with SessionLocal() as db:
            return list(
                db.execute(
                    select(RouteRequest).where(RouteRequest.user_id == user_id).order_by(RouteRequest.requested_at.desc())
                ).scalars().all()
            )
