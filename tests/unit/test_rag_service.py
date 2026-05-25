from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import (
    IntentClassificationException,
    LLMUnavailableException,
    RetrieverException,
)
from app.core.logging import request_id_ctx_var
from app.models.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService


@pytest.fixture
def mock_retriever(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_llm(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_intent_classifier(mocker):
    classifier = mocker.MagicMock()
    classifier.classify = AsyncMock(return_value="policy")
    return classifier


@pytest.fixture
def chat_request():
    return ChatRequest(query="test query", user_id="123", conversation_id="conv-1")


@pytest.mark.asyncio
async def test_answer_routes_to_crag_on_policy_intent(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.return_value = "policy"
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    rag_service._run_crag_pipeline = AsyncMock(
        return_value=ChatResponse(
            response="crag response", request_id="req-1", conversation_id="conv-1"
        )
    )
    rag_service._run_agentic_pipeline = AsyncMock()

    response = await rag_service.answer(chat_request)

    assert response.response == "crag response"
    rag_service._run_crag_pipeline.assert_called_once_with(chat_request, "test query")
    rag_service._run_agentic_pipeline.assert_not_called()


@pytest.mark.asyncio
async def test_answer_routes_to_agentic_on_user_data_intent(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.return_value = "user_data"
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    rag_service._run_crag_pipeline = AsyncMock()
    rag_service._run_agentic_pipeline = AsyncMock(
        return_value=ChatResponse(
            response="agent response", request_id="req-1", conversation_id="conv-1"
        )
    )

    response = await rag_service.answer(chat_request)

    assert response.response == "agent response"
    rag_service._run_agentic_pipeline.assert_called_once_with(chat_request, "test query")
    rag_service._run_crag_pipeline.assert_not_called()


@pytest.mark.asyncio
async def test_answer_defaults_to_policy_on_classification_failure(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.side_effect = IntentClassificationException(
        message="fail", detail="fail"
    )
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    rag_service._run_crag_pipeline = AsyncMock(
        return_value=ChatResponse(
            response="crag response", request_id="req-1", conversation_id="conv-1"
        )
    )
    rag_service._run_agentic_pipeline = AsyncMock()

    response = await rag_service.answer(chat_request)

    assert response.response == "crag response"
    rag_service._run_crag_pipeline.assert_called_once_with(chat_request, "test query")
    rag_service._run_agentic_pipeline.assert_not_called()


@pytest.mark.asyncio
async def test_answer_returns_chat_response(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.return_value = "policy"
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    mock_chain = mocker.MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value="real response")

    with patch("app.pipelines.crag_pipeline.build_crag_chain", return_value=mock_chain):
        request_id_ctx_var.set("test-req-id")
        response = await rag_service.answer(chat_request)

        assert isinstance(response, ChatResponse)
        assert response.response == "real response"
        assert response.conversation_id == "conv-1"
        assert response.request_id == "test-req-id"


@pytest.mark.asyncio
async def test_answer_propagates_retriever_exception(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.return_value = "policy"
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    mock_chain = mocker.MagicMock()
    mock_chain.ainvoke.side_effect = RetrieverException(message="retriever err", detail="err")

    with patch("app.pipelines.crag_pipeline.build_crag_chain", return_value=mock_chain):
        with pytest.raises(RetrieverException):
            await rag_service.answer(chat_request)


@pytest.mark.asyncio
async def test_answer_propagates_llm_exception(
    mock_retriever, mock_llm, mock_intent_classifier, chat_request, mocker
):
    mock_intent_classifier.classify.return_value = "policy"
    rag_service = RAGService(mock_retriever, mock_llm, mock_intent_classifier)

    mock_chain = mocker.MagicMock()
    mock_chain.ainvoke.side_effect = LLMUnavailableException(message="llm err", detail="err")

    with patch("app.pipelines.crag_pipeline.build_crag_chain", return_value=mock_chain):
        with pytest.raises(LLMUnavailableException):
            await rag_service.answer(chat_request)
