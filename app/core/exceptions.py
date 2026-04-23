class RAGServiceException(Exception):
    """Base exception for all TM-RAG service errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, detail={self.detail!r})"


class LLMUnavailableException(RAGServiceException):
    """Raised when the NVIDIA AI Endpoints API is unreachable or returns an error."""

    def __init__(
        self,
        message: str = "LLM service is currently unavailable.",
        detail: str | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class RetrieverException(RAGServiceException):
    """Raised when pgvector or FAISS retrieval fails."""

    def __init__(
        self,
        message: str = "An error occurred during document retrieval.",
        detail: str | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class DocumentNotFoundException(RAGServiceException):
    """Raised when retrieval returns no relevant documents for a query."""

    def __init__(
        self,
        message: str = "No relevant documents found for the given query.",
        detail: str | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class IngestException(RAGServiceException):
    """Raised when document ingestion into the vector store fails."""

    def __init__(
        self,
        message: str = "An error occurred during document ingestion.",
        detail: str | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)
