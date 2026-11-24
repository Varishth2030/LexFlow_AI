from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check application operational status and database connectivity.",
)
def check_health(db: Session = Depends(get_db)):
    try:
        # Validate database connectivity by executing a lightweight query
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": f"error: {str(e)}",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
            },
        )

    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
