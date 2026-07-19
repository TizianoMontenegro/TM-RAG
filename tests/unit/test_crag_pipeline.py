from unittest.mock import AsyncMock

import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from app.core.exceptions import DocumentNotFoundException
from app.pipelines.crag_pipeline import build_crag_chain


@pytest.fixture
def mock_retriever_service(mocker):
    service = mocker.MagicMock()
    service.retrieve_cold_only = AsyncMock(
        return_value=[
            Document(page_content="Baggage policy: one free checked bag."),
            Document(page_content="Fare rules: non-refundable tickets."),
        ]
    )
    return service


@pytest.fixture
def mock_embedding_model(mocker):
    model = mocker.MagicMock()
    model.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return model


@pytest.mark.asyncio
async def test_crag_generates_on_relevant_docs(
    mock_retriever_service, mock_embedding_model, mocker
):
    json_llm = RunnableLambda(lambda x: '{"score": "relevant"}')
    llm = RunnableLambda(lambda x: "Baggage allows one free bag.")

    service = mocker.MagicMock()
    service.get_json_client.return_value = json_llm
    service.get_client.return_value = llm

    chain = build_crag_chain(mock_retriever_service, service, mock_embedding_model)
    result = await chain.ainvoke("What is the baggage policy?")

    assert result == "Baggage allows one free bag."
    mock_retriever_service.retrieve_cold_only.assert_called_once_with([0.1, 0.2, 0.3], top_k=20)


@pytest.mark.asyncio
async def test_crag_widens_search_when_none_relevant(
    mock_retriever_service, mock_embedding_model, mocker
):
    json_llm = RunnableLambda(lambda x: '{"score": "not_relevant"}')

    service = mocker.MagicMock()
    service.get_json_client.return_value = json_llm
    service.get_client.return_value = RunnableLambda(lambda x: "")

    chain = build_crag_chain(mock_retriever_service, service, mock_embedding_model)

    with pytest.raises(DocumentNotFoundException):
        await chain.ainvoke("What is the pet policy?")

    assert mock_retriever_service.retrieve_cold_only.call_count == 2
    mock_retriever_service.retrieve_cold_only.assert_any_call([0.1, 0.2, 0.3], top_k=20)
    mock_retriever_service.retrieve_cold_only.assert_any_call([0.1, 0.2, 0.3], top_k=40)


@pytest.mark.asyncio
async def test_crag_raises_when_no_relevant_after_widen(
    mock_retriever_service, mock_embedding_model, mocker
):
    json_llm = RunnableLambda(lambda x: '{"score": "not_relevant"}')

    service = mocker.MagicMock()
    service.get_json_client.return_value = json_llm
    service.get_client.return_value = RunnableLambda(lambda x: "")

    chain = build_crag_chain(mock_retriever_service, service, mock_embedding_model)

    with pytest.raises(DocumentNotFoundException):
        await chain.ainvoke("What is the alien abduction policy?")

    assert mock_retriever_service.retrieve_cold_only.call_count == 2
