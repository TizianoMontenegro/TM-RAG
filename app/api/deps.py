from fastapi import Depends

from app.core.config import settings
from app.repositories.base import VectorStoreRepository

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def get_settings() -> settings.__class__:
    return settings


# ---------------------------------------------------------------------------
# Repository stubs (Phase 3 not yet implemented)
# These return working objects that raise NotImplementedError if used.
# ---------------------------------------------------------------------------


class _StubRepository(VectorStoreRepository):
    """Stub repository that satisfies the interface without a backend."""

    async def search(self, query_vector: list[float], top_k: int) -> list:
        raise NotImplementedError(
            "FAISSRepository/PgVectorRepository not yet implemented. See Phase 3."
        )

    async def upsert(self, documents: list) -> None:
        raise NotImplementedError(
            "FAISSRepository/PgVectorRepository not yet implemented. See Phase 3."
        )

    async def delete(self, ids: list[str]) -> None:
        raise NotImplementedError(
            "FAISSRepository/PgVectorRepository not yet implemented. See Phase 3."
        )


def get_hot_repository() -> VectorStoreRepository:
    return _StubRepository()


def get_cold_repository() -> VectorStoreRepository:
    return _StubRepository()


# ---------------------------------------------------------------------------
# Service stubs (Phase 5 not yet implemented)
# These return working objects that raise NotImplementedError if used.
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
