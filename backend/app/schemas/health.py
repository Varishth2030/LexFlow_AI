from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    message: str = Field(..., description="Welcome message")
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    docs_url: str = Field(..., description="URL for API documentation")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection health")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Runtime environment")
