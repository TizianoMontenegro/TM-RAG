from langchain_core.documents import Document

from app.core.exceptions import IngestException
from app.repositories.base import VectorStoreRepository


async def run_ingest(
    documents: list[Document], repository: VectorStoreRepository
) -> None:
    """Ingest documents into the vector store.

    Args:
        documents: List of LangChain Document objects to ingest.
        repository: The vector store repository to ingest into.

    Raises:
        IngestException: If ingestion fails.
    """
    try:
        await repository.upsert(documents)
    except Exception as e:
        raise IngestException(
            message="An error occurred during document ingestion.",
            detail=str(e),
        ) from e
