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
