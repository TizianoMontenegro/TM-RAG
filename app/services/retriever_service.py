from langchain_core.documents import Document

from app.core.exceptions import DocumentNotFoundException, RetrieverException
from app.repositories.base import VectorStoreRepository


class RetrieverService:
    def __init__(
        self,
        hot_repo: VectorStoreRepository,
        cold_repo: VectorStoreRepository,
    ) -> None:
        self.hot_repo = hot_repo
        self.cold_repo = cold_repo

    async def retrieve(
        self, query_vector: list[float], hot: bool = False, top_k: int = 20
    ) -> list[Document]:
        """Retrieve documents from the appropriate repository.

        Args:
            query_vector: The query embedding vector.
            hot: If True, use hot (FAISS) repository. Defaults to False (cold/pgvector).
            top_k: Number of results to return. Defaults to 20.

        Returns:
            List of retrieved Document objects.

        Raises:
            RetrieverException: If retrieval fails.
            DocumentNotFoundException: If no documents are found.
        """
        try:
            if hot:
                docs = await self.hot_repo.search(query_vector, top_k=5)
            else:
                # Cold path: fetch broad candidates from pgvector, then re-rank via FAISS
                candidates = await self.cold_repo.search(query_vector, top_k=top_k)
                if not candidates:
                    raise DocumentNotFoundException()
                docs = await self.hot_repo.rerank(candidates, query_vector, top_k=5)

            if not docs:
                raise DocumentNotFoundException()
            return docs
        except (RetrieverException, DocumentNotFoundException):
            raise
        except Exception as e:
            raise RetrieverException(
                message="An error occurred during document retrieval.",
                detail=str(e),
            ) from e

    async def retrieve_cold_only(
        self, query_vector: list[float], top_k: int = 20
    ) -> list[Document]:
        """Retrieve from cold store only (used by CRAG pipeline).

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return. Defaults to 20.

        Returns:
            List of retrieved Document objects.

        Raises:
            RetrieverException: If retrieval fails.
            DocumentNotFoundException: If no documents are found.
        """
        try:
            docs = await self.cold_repo.search(query_vector, top_k=top_k)
            if not docs:
                raise DocumentNotFoundException()
            return docs
        except (RetrieverException, DocumentNotFoundException):
            raise
        except Exception as e:
            raise RetrieverException(
                message="An error occurred during document retrieval.",
                detail=str(e),
            ) from e
