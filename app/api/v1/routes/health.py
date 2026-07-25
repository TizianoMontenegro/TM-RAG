import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import check_nvidia, check_pgvector, get_readiness_service
from app.core.config import settings
from app.core.logging import request_id_ctx_var
from app.models.common import HealthResponse, ReadinessResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint — no auth, no DB/LLM calls."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(
    llm_service: LLMService = Depends(get_readiness_service),
) -> ReadinessResponse:
    """Readiness check — verifies pgvector and NVIDIA connectivity."""
    pgvector_result, nvidia_result = await asyncio.gather(
        check_pgvector(),
        check_nvidia(llm_service),
    )

    checks = {"pgvector": pgvector_result, "nvidia": nvidia_result}
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    response = ReadinessResponse(
        status=status,
        version=settings.app_version,
        checks=checks,
        request_id=request_id_ctx_var.get(),
    )

    if status == "degraded":
        return JSONResponse(status_code=503, content=response.model_dump())

    return response
