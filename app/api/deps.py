from fastapi import Depends

from app.core.config import settings
from app.repositories.base import VectorStoreRepository
from app.repositories.faiss_repository import FAISSRepository
from app.repositories.pgvector_repository import PgVectorRepository
from app.services.intent_classifier import IntentClassifier
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.retriever_service import RetrieverService

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
# Services
# ---------------------------------------------------------------------------


def get_retriever_service(
    hot_repo: VectorStoreRepository = Depends(get_hot_repository),
    cold_repo: VectorStoreRepository = Depends(get_cold_repository),
) -> RetrieverService:
    return RetrieverService(hot_repo=hot_repo, cold_repo=cold_repo)


def get_llm_service(
    settings: settings.__class__ = Depends(get_settings),
) -> LLMService:
    return LLMService(settings=settings)


def get_intent_classifier(
    llm: LLMService = Depends(get_llm_service),
) -> IntentClassifier:
    return IntentClassifier(llm=llm)


def get_rag_service(
    retriever: RetrieverService = Depends(get_retriever_service),
    llm: LLMService = Depends(get_llm_service),
    intent_classifier: IntentClassifier = Depends(get_intent_classifier),
    embedding_model=Depends(get_embedding_model),
) -> RAGService:
    return RAGService(
        retriever=retriever,
        llm=llm,
        intent_classifier=intent_classifier,
        embedding_model=embedding_model,
    )
