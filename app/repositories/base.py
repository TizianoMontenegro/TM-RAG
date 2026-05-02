from abc import ABC, abstractmethod
from langchain_core.documents import Document


class VectorStoreRepository(ABC):
    """Abstract base class defining the VectorStoreRepository contract."""

    @abstractmethod
    async def search(self, query_vector: list[float], top_k: int) -> list[Document]:
        """Return the top_k most similar documents to query_vector."""
        ...

    @abstractmethod
    async def upsert(self, documents: list[Document]) -> None:
        """Insert or update documents in the store."""
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Remove documents by ID."""
        ...

    @abstractmethod
    async def rerank(
        self, candidates: list[Document], query_vector: list[float], top_k: int
    ) -> list[Document]:
        """Re-rank candidates using query vector.

        For FAISS: builds a temporary index from candidates and searches within it.
        For PgVector: raises RetrieverException (not supported).
        """
        ...
