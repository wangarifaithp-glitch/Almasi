import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.errors import database_error_code
from app.db.session import get_db
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", summary="Check API and database readiness", response_model=None)
def health_check(db: Session = Depends(get_db)) -> dict[str, str] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        existing_tables = set(inspect(db.get_bind()).get_table_names())
    except SQLAlchemyError as exc:
        error_code = database_error_code(exc)
        logger.error(
            "Database readiness check failed (%s, code=%s)",
            type(exc).__name__,
            error_code,
        )
        detail = (
            "MySQL rejected the configured account. Check its password, permitted host, and database grants."
            if error_code == 1045
            else "Cannot connect to the configured database."
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "unavailable",
                "detail": detail,
            },
        )

    missing_tables = sorted(set(User.metadata.tables) - existing_tables)
    if missing_tables:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "not_ready",
                "detail": "Database schema is incomplete. Run the migrations.",
                "missing_tables": missing_tables,
            },
        )

    return {"status": "healthy", "database": "connected"}
