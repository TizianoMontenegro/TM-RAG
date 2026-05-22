import pytest
from unittest.mock import AsyncMock
from langchain_core.messages import AIMessage

from app.services.intent_classifier import IntentClassifier
from app.core.exceptions import IntentClassificationException

@pytest.fixture
def mock_llm_service(mocker):
    mock_service = mocker.MagicMock()
    mock_client = mocker.MagicMock()
    mock_client.ainvoke = AsyncMock()
    mock_service.get_json_client.return_value = mock_client
    return mock_service

@pytest.mark.asyncio
async def test_classify_returns_user_data(mock_llm_service):
    mock_llm_service.get_json_client().ainvoke.return_value = AIMessage(content='{"intent": "user_data"}')
    classifier = IntentClassifier(mock_llm_service)
    intent = await classifier.classify("my booking status")
    assert intent == "user_data"

@pytest.mark.asyncio
async def test_classify_returns_policy(mock_llm_service):
    mock_llm_service.get_json_client().ainvoke.return_value = AIMessage(content='{"intent": "policy"}')
    classifier = IntentClassifier(mock_llm_service)
    intent = await classifier.classify("how much for extra bag")
    assert intent == "policy"

@pytest.mark.asyncio
async def test_classify_raises_on_invalid_response(mock_llm_service):
    mock_llm_service.get_json_client().ainvoke.return_value = AIMessage(content='not a json')
    classifier = IntentClassifier(mock_llm_service)
    with pytest.raises(IntentClassificationException) as exc:
        await classifier.classify("hello")
    assert "Unable to determine query type" in exc.value.message

@pytest.mark.asyncio
async def test_classify_raises_on_unknown_intent_value(mock_llm_service):
    mock_llm_service.get_json_client().ainvoke.return_value = AIMessage(content='{"intent": "unknown"}')
    classifier = IntentClassifier(mock_llm_service)
    with pytest.raises(IntentClassificationException) as exc:
        await classifier.classify("hello")
    assert "Unable to determine query type" in exc.value.message
    assert "Invalid intent value: unknown" in exc.value.detail
