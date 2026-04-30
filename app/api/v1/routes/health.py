from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.common import HealthResponse
from app.core.config import settings

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint — no auth, no DB/LLM calls."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )
