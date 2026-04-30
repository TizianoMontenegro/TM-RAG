from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    IngestException,
    LLMUnavailableException,
    RetrieverException,
    RAGServiceException,
)
from app.core.logging import request_id_ctx_var, setup_logging
from app.api.middleware import RequestIDMiddleware
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.chat import router as chat_router


EXCEPTION_STATUS_MAP: dict[type[RAGServiceException], int] = {
    DocumentNotFoundException: 404,
    LLMUnavailableException: 503,
    RetrieverException: 502,
    IngestException: 500,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(chat_router)


@app.exception_handler(RAGServiceException)
async def rag_exception_handler(
    request: Request, exc: RAGServiceException
) -> JSONResponse:
    from app.models.common import ErrorResponse

    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.message,
            request_id=request_id_ctx_var.get(),
        ).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
