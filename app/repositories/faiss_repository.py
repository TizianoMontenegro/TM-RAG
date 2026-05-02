from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document

from app.core.exceptions import RetrieverException
from app.repositories.base import VectorStoreRepository

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


class FAISSRepository(VectorStoreRepository):
    """Hot store — in-memory FAISS backend via LangChain FAISS.

    Index is built lazily on first upsert() or search().
    No persistence to disk — in-memory only.
    """

    def __init__(
        self,
        embedding_model: Embeddings | None = None,
    ) -> None:
        self._embedding_model = embedding_model
        self._vectorstore: FAISS | None = None
        self._doc_ids: list[str] = []

    def _get_embedding_model(self) -> Embeddings:
        if self._embedding_model is None:
            raise RetrieverException(
                detail="embedding_model is required to use FAISSRepository"
            )
        return self._embedding_model

    def _ensure_vectorstore(self, documents: list[Document] | None = None) -> FAISS:
        if self._vectorstore is not None:
            return self._vectorstore

        embedding_model = self._get_embedding_model()

        if documents:
            try:
                self._vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=embedding_model,
                )
            except Exception as exc:
                raise RetrieverException(
                    detail=f"Failed to build FAISS index: {exc}"
                ) from exc
        else:
            try:
                self._vectorstore = FAISS.from_texts(
                    texts=[""], embedding=embedding_model
                )
                self._vectorstore.delete(
                    [list(self._vectorstore.index_to_docstore_id.values())[0]]
                )
            except Exception as exc:
                raise RetrieverException(
                    detail=f"Failed to initialize empty FAISS index: {exc}"
                ) from exc

        return self._vectorstore

    async def search(self, query_vector: list[float], top_k: int) -> list[Document]:
        def _search() -> list[Document]:
            try:
                vs = self._ensure_vectorstore()
                return vs.similarity_search_by_vector(
                    embedding=query_vector,
                    k=top_k,
                )
            except RetrieverException:
                raise
            except Exception as exc:
                raise RetrieverException(detail=f"FAISS search failed: {exc}") from exc

        return await asyncio.to_thread(_search)

    async def upsert(self, documents: list[Document]) -> None:
        def _upsert() -> None:
            try:
                if self._vectorstore is None:
                    self._ensure_vectorstore(documents)
                    return

                self._vectorstore.add_documents(documents=documents)
            except RetrieverException:
                raise
            except Exception as exc:
                raise RetrieverException(detail=f"FAISS upsert failed: {exc}") from exc

        await asyncio.to_thread(_upsert)

    async def delete(self, ids: list[str]) -> None:
        def _delete() -> None:
            try:
                if self._vectorstore is None:
                    return
                self._vectorstore.delete(ids=ids)
            except Exception as exc:
                raise RetrieverException(detail=f"FAISS delete failed: {exc}") from exc

        await asyncio.to_thread(_delete)

    async def rerank(
        self, candidates: list[Document], query_vector: list[float], top_k: int
    ) -> list[Document]:
        """Build a temporary FAISS index from candidates and search within it.

        This implements cold-path re-ranking: the candidate set comes from pgvector,
        and we re-rank only within that subset using FAISS similarity search.
        """
        if not candidates:
            return []

        def _rerank() -> list[Document]:
            try:
                embedding_model = self._get_embedding_model()
                temp_index = FAISS.from_documents(
                    documents=candidates,
                    embedding=embedding_model,
                )
                return temp_index.similarity_search_by_vector(
                    embedding=query_vector,
                    k=min(top_k, len(candidates)),
                )
            except Exception as exc:
                raise RetrieverException(detail=f"FAISS rerank failed: {exc}") from exc

        return await asyncio.to_thread(_rerank)
