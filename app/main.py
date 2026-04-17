from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import create_db_and_tables
from app.services.user_service import seed_initial_data

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_starting", extra={"env": settings.app_env})
    if settings.weather_api_key is None or not settings.weather_api_key.get_secret_value().strip():
        logger.warning(
            "weather_api_key_missing",
            extra={
                "impact": "GET /api/v1/weather/current will return configuration error until WEATHER_API_KEY is set"
            },
        )
    if settings.auto_create_tables and settings.app_env != "testing":
        create_db_and_tables()
    if settings.app_env != "testing":
        seed_initial_data()
    yield
    logger.info("application_stopping")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
