from fastapi import Depends

from app.core.config import settings
from app.repositories.base import VectorStoreRepository
from app.repositories.faiss_repository import FAISSRepository
from app.repositories.pgvector_repository import PgVectorRepository

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def get_settings() -> settings.__class__:
    return settings


# ---------------------------------------------------------------------------
# Embedding model (shared by both repositories)
# ---------------------------------------------------------------------------

_embedding_model_cache = None


def get_embedding_model():
    global _embedding_model_cache
    if _embedding_model_cache is None:
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

        _embedding_model_cache = NVIDIAEmbeddings(
            model=settings.nvidia_embedding_model,
            api_key=settings.nvidia_api_key.get_secret_value(),
            base_url=settings.nvidia_base_url,
        )
    return _embedding_model_cache


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


def get_hot_repository(
    embedding_model=Depends(get_embedding_model),
) -> VectorStoreRepository:
    return FAISSRepository(embedding_model=embedding_model)


def get_cold_repository(
    embedding_model=Depends(get_embedding_model),
) -> VectorStoreRepository:
    return PgVectorRepository(embedding_model=embedding_model)


# ---------------------------------------------------------------------------
# Service stubs (Phase 5 not yet implemented)
# ---------------------------------------------------------------------------


class _StubRetrieverService:
    """Stub retriever service."""

    def __init__(
        self, hot_repo: VectorStoreRepository, cold_repo: VectorStoreRepository
    ):
        self.hot_repo = hot_repo
        self.cold_repo = cold_repo

    async def retrieve(self, query_vector: list[float], hot: bool = False) -> list:
        raise NotImplementedError("RetrieverService not yet implemented. See Phase 5.")


class _StubLLMService:
    """Stub LLM service."""

    def __init__(self, settings):
        self.settings = settings

    def get_client(self):
        raise NotImplementedError("LLMService not yet implemented. See Phase 5.")


class _StubRAGService:
    """Stub RAG service — placeholder until Phase 5."""

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    async def answer(self, request) -> dict:
        raise NotImplementedError("RAGService not yet implemented. See Phase 5.")


def get_retriever_service(
    hot_repo: VectorStoreRepository = Depends(get_hot_repository),
    cold_repo: VectorStoreRepository = Depends(get_cold_repository),
) -> _StubRetrieverService:
    return _StubRetrieverService(hot_repo=hot_repo, cold_repo=cold_repo)


def get_llm_service(
    settings: settings.__class__ = Depends(get_settings),
) -> _StubLLMService:
    return _StubLLMService(settings=settings)


def get_rag_service(
    retriever=Depends(get_retriever_service),
    llm=Depends(get_llm_service),
) -> _StubRAGService:
    return _StubRAGService(retriever=retriever, llm=llm)
