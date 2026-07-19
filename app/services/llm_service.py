from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.config import settings
from app.core.exceptions import LLMUnavailableException


class LLMService:
    def __init__(self, settings: settings.__class__ = settings) -> None:
        try:
            self._client = ChatNVIDIA(
                model=settings.nvidia_llm_model,
                api_key=settings.nvidia_api_key.get_secret_value(),
                temperature=settings.nvidia_temperature,
                base_url=settings.nvidia_base_url,
            )
        except Exception as e:
            raise LLMUnavailableException(
                message="LLM service is currently unavailable.",
                detail=str(e),
            ) from e

    def get_client(self) -> ChatNVIDIA:
        return self._client

    def get_json_client(self) -> ChatNVIDIA:
        """Return LLM configured for JSON output (used by intent classifier, relevance grader)."""
        return ChatNVIDIA(
            model=settings.nvidia_llm_model,
            api_key=settings.nvidia_api_key.get_secret_value(),
            temperature=0.0,
            base_url=settings.nvidia_base_url,
        )
