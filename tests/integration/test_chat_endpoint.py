import pytest
from unittest.mock import AsyncMock

from app.core.exceptions import LLMUnavailableException, DocumentNotFoundException
from app.models.chat import ChatResponse

@pytest.mark.asyncio
async def test_chat_returns_200(async_client, mocker):
    mock_rag = mocker.MagicMock()
    mock_rag.answer = AsyncMock(return_value=ChatResponse(
        response="test response",
        conversation_id="conv-1",
        request_id="req-1"
    ))
    
    from main import app
    from app.api.deps import get_rag_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    
    response = await async_client.post("/v1/chat", json={
        "query": "hello",
        "user_id": "user1"
    })
    
    app.dependency_overrides.pop(get_rag_service, None)
    
    assert response.status_code == 200
    assert response.json()["response"] == "test response"

@pytest.mark.asyncio
async def test_chat_propagates_request_id(async_client, mocker):
    mock_rag = mocker.MagicMock()
    mock_rag.answer = AsyncMock(return_value=ChatResponse(
        response="test response",
        conversation_id="conv-1",
        request_id="test-req-id"
    ))
    
    from main import app
    from app.api.deps import get_rag_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    
    response = await async_client.post("/v1/chat", json={
        "query": "hello",
        "user_id": "user1"
    }, headers={"X-Request-ID": "test-req-id"})
    
    app.dependency_overrides.pop(get_rag_service, None)
    
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "test-req-id"

@pytest.mark.asyncio
async def test_chat_returns_503_on_llm_failure(async_client, mocker):
    mock_rag = mocker.MagicMock()
    mock_rag.answer.side_effect = LLMUnavailableException(message="llm error", detail="detail")
    
    from main import app
    from app.api.deps import get_rag_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    
    response = await async_client.post("/v1/chat", json={
        "query": "hello",
        "user_id": "user1"
    })
    
    app.dependency_overrides.pop(get_rag_service, None)
    
    assert response.status_code == 503
    assert "llm error" in response.json()["error"]

@pytest.mark.asyncio
async def test_chat_returns_404_on_no_documents(async_client, mocker):
    mock_rag = mocker.MagicMock()
    mock_rag.answer.side_effect = DocumentNotFoundException(message="not found", detail="detail")
    
    from main import app
    from app.api.deps import get_rag_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    
    response = await async_client.post("/v1/chat", json={
        "query": "hello",
        "user_id": "user1"
    })
    
    app.dependency_overrides.pop(get_rag_service, None)
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"]

@pytest.mark.asyncio
async def test_chat_rejects_empty_query(async_client):
    response = await async_client.post("/v1/chat", json={
        "query": "",
        "user_id": "user1"
    })
    assert response.status_code == 422
