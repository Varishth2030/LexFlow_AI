import sys
from pathlib import Path

# Ensure backend directory is in sys.path so app modules can be resolved regardless of CWD
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.api import api_router
from app.core.config import settings
from app.schemas.health import HealthCheckResponse, RootResponse

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for LexFlow AI - Case Management and Workflow Automation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration for React frontend (Vite / Create-React-App)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="Root",
    tags=["Root"],
)
def root():
    """
    Root endpoint returning general API information.
    """
    return RootResponse(
        message=f"Welcome to {settings.PROJECT_NAME} API",
        status="online",
        version=settings.VERSION,
        docs_url="/docs",
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Application and Database Health Check",
    tags=["Health"],
)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint verifying API readiness and SQLite database connectivity.
    """
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
