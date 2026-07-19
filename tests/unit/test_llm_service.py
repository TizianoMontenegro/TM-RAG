import pytest
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.config import Settings
from app.core.exceptions import LLMUnavailableException
from app.services.llm_service import LLMService


def test_get_client_returns_chat_nvidia(mock_settings: Settings):
    service = LLMService(settings=mock_settings)
    client = service.get_client()
    assert isinstance(client, ChatNVIDIA)
    assert client.temperature == 0.0


def test_get_json_client_returns_zero_temperature(mock_settings: Settings):
    service = LLMService(settings=mock_settings)
    json_client = service.get_json_client()
    assert isinstance(json_client, ChatNVIDIA)
    assert json_client.temperature == 0.0


def test_llm_unavailable_exception_on_api_error(mock_settings: Settings, mocker):
    mocker.patch(
        "app.services.llm_service.ChatNVIDIA",
        side_effect=ConnectionError("Cannot reach NVIDIA API"),
    )
    with pytest.raises(LLMUnavailableException) as exc_info:
        LLMService(settings=mock_settings)

    assert "LLM service is currently unavailable." in str(exc_info.value.message)
