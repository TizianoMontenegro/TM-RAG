from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document

from app.core.config import settings
from app.core.exceptions import RetrieverException
from app.repositories.base import VectorStoreRepository

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


class PgVectorRepository(VectorStoreRepository):
    """Cold store — persistent pgvector backend via LangChain PGVector."""

    def __init__(
        self,
        embedding_model: Embeddings | None = None,
        connection_string: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._embedding_model = embedding_model
        self._connection_string = connection_string or settings.database_url
        self._collection_name = collection_name or settings.pgvector_collection_name
        self._vectorstore: PGVector | None = None

    def _get_vectorstore(self) -> PGVector:
        if self._vectorstore is None:
            if self._embedding_model is None:
                raise RetrieverException(
                    detail="embedding_model is required to initialize PGVector"
                )
            try:
                self._vectorstore = PGVector(
                    connection_string=self._connection_string,
                    embedding_function=self._embedding_model,
                    collection_name=self._collection_name,
                    use_jsonb=True,
                )
            except Exception as exc:
                raise RetrieverException(
                    detail=f"Failed to initialize PGVector: {exc}"
                ) from exc
        return self._vectorstore

    async def search(self, query_vector: list[float], top_k: int) -> list[Document]:
        def _search() -> list[Document]:
            try:
                return self._get_vectorstore().similarity_search_by_vector(
                    embedding=query_vector,
                    k=top_k,
                )
            except Exception as exc:
                raise RetrieverException(
                    detail=f"PgVector search failed: {exc}"
                ) from exc

        return await asyncio.to_thread(_search)

    async def upsert(self, documents: list[Document]) -> None:
        def _upsert() -> None:
            try:
                self._get_vectorstore().add_documents(documents=documents)
            except Exception as exc:
                raise RetrieverException(
                    detail=f"PgVector upsert failed: {exc}"
                ) from exc

        await asyncio.to_thread(_upsert)

    async def delete(self, ids: list[str]) -> None:
        def _delete() -> None:
            try:
                self._get_vectorstore().delete(ids=ids)
            except Exception as exc:
                raise RetrieverException(
                    detail=f"PgVector delete failed: {exc}"
                ) from exc

        await asyncio.to_thread(_delete)

    async def rerank(
        self, candidates: list[Document], query_vector: list[float], top_k: int
    ) -> list[Document]:
        raise RetrieverException(
            message="Re-ranking is not supported by PgVectorRepository.",
            detail="Use FAISSRepository.rerank() for candidate re-ranking.",
        )
