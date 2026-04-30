from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = "ok"
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Response model for error responses.

    Note: Never include exception.detail - that stays in logs only.
    """

    error: str
    request_id: str
