from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    IngestException,
    LLMUnavailableException,
    RetrieverException,
    RAGServiceException,
)
from app.core.logging import setup_logging
from app.api.middleware import RequestIDMiddleware


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


@app.exception_handler(RAGServiceException)
async def rag_exception_handler(request: Request, exc: RAGServiceException) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"message": exc.message},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)