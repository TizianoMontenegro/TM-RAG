import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.chat import ChatRequest, ChatResponse
from app.models.common import ErrorResponse
from app.core.logging import request_id_ctx_var
from app.core.exceptions import (
    RAGServiceException,
    DocumentNotFoundException,
    LLMUnavailableException,
)
from app.api.deps import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service=Depends(get_rag_service),
) -> ChatResponse:
    """Chat endpoint — returns placeholder response until RAG is wired.

    TODO: wire RAGService - replace placeholder with actual rag_service.answer(request)
    """
    try:
        # Placeholder response - RAGService not yet implemented
        return ChatResponse(
            response="This is a placeholder response. RAG service not yet wired.",
            conversation_id=request.conversation_id or "new-conversation",
            sources=None,
            request_id=request_id_ctx_var.get(),
        )
    except DocumentNotFoundException as exc:
        logger.exception("Document not found")
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=exc.message,
                request_id=request_id_ctx_var.get(),
            ).model_dump(),
        )
    except LLMUnavailableException as exc:
        logger.exception("LLM unavailable")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=exc.message,
                request_id=request_id_ctx_var.get(),
            ).model_dump(),
        )
    except RAGServiceException as exc:
        logger.exception("RAG service error")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=exc.message,
                request_id=request_id_ctx_var.get(),
            ).model_dump(),
        )
