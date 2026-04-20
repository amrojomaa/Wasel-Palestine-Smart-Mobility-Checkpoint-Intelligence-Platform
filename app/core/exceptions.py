from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class AppException(Exception):
    status_code = 400
    code = "APP_ERROR"

    def __init__(self, message: str, details: list[dict] | None = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class UnauthorizedException(AppException):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenException(AppException):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundException(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ConflictException(AppException):
    status_code = 409
    code = "CONFLICT"


class RateLimitedException(AppException):
    status_code = 429
    code = "RATE_LIMITED"


class ServiceConfigurationException(AppException):
    """Raised when optional integration settings are missing (e.g. WEATHER_API_KEY)."""

    status_code = 503
    code = "SERVICE_NOT_CONFIGURED"


class UpstreamServiceException(AppException):
    status_code = 503
    code = "UPSTREAM_UNAVAILABLE"


def _error_payload(code: str, message: str, details: list[dict] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        details = [{"field": str(err.get("loc")), "issue": err.get("msg")} for err in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_error_payload("VALIDATION_ERROR", "Invalid request payload", details),
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_exception_handler(_: Request, __: SQLAlchemyError):
        return JSONResponse(
            status_code=500,
            content=_error_payload("DATABASE_ERROR", "Database operation failed"),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_: Request, __: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_payload("INTERNAL_ERROR", "Unexpected server error"),
        )
