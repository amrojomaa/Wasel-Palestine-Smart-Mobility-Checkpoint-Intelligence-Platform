from fastapi import APIRouter

from app.api.v1.endpoints import alerts, auth, checkpoints, graphql, health, incidents, moderation, reports, routes, users, weather

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["F09 - Health and Operational Checks"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["F01 - Identity and Access (Auth)"])
api_v1_router.include_router(users.router, prefix="/users", tags=["F01 - Identity and Access (RBAC)"])
api_v1_router.include_router(checkpoints.router, prefix="/checkpoints", tags=["F02 - Checkpoints Management"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["F03 - Incidents Lifecycle and Verification"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["F04 - Crowdsourced Reports and Voting"])
api_v1_router.include_router(moderation.router, prefix="/moderation", tags=["F05 - Moderation and Abuse Controls"])
api_v1_router.include_router(routes.router, prefix="/routes", tags=["F07 - Routing and Geocoding"])
api_v1_router.include_router(alerts.router, prefix="/alerts", tags=["F06 - Alerts and Subscriptions"])
api_v1_router.include_router(weather.router, prefix="/weather", tags=["F08 - Weather Integration"])
api_v1_router.include_router(graphql.router, prefix="/graphql", tags=["F10 - GraphQL Bonus"])
