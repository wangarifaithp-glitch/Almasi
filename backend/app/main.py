import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.db.errors import database_error_code

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Rejected invalid request for %s", request.url.path)
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "location": error["loc"],
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error(
        "Database operation failed for %s (%s, code=%s)",
        request.url.path,
        type(exc).__name__,
        database_error_code(exc),
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database is unavailable or not initialized. Check DATABASE_URL and apply the database migrations."
        },
    )
