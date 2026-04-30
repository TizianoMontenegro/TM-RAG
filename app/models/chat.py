from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str = Field(
        ..., min_length=1, max_length=2000, description="User's question"
    )
    user_id: str = Field(
        ..., min_length=1, description="Opaque identifier from TM-Backend"
    )
    conversation_id: str | None = None


class Source(BaseModel):
    """Source document reference for chat responses."""

    document_id: str
    excerpt: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    conversation_id: str
    sources: list[Source] | None = None
    request_id: str
