from fastapi import APIRouter

from app.api.v1.endpoints import alerts, auth, checkpoints, graphql, health, incidents, moderation, reports, routes, users, weather

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(checkpoints.router, prefix="/checkpoints", tags=["Checkpoints"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(moderation.router, prefix="/moderation", tags=["Moderation"])
api_v1_router.include_router(routes.router, prefix="/routes", tags=["Routing"])
api_v1_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_v1_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_v1_router.include_router(graphql.router, prefix="/graphql", tags=["GraphQL"])
