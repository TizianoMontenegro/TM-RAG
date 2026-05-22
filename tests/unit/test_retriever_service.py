import pytest
from unittest.mock import AsyncMock
from langchain_core.documents import Document

from app.services.retriever_service import RetrieverService
from app.core.exceptions import DocumentNotFoundException

@pytest.fixture
def mock_hot_repo(mocker):
    repo = mocker.MagicMock()
    repo.search = AsyncMock()
    repo.rerank = AsyncMock()
    return repo

@pytest.fixture
def mock_cold_repo(mocker):
    repo = mocker.MagicMock()
    repo.search = AsyncMock()
    return repo

@pytest.mark.asyncio
async def test_retrieve_cold_path(mock_hot_repo, mock_cold_repo):
    mock_cold_repo.search.return_value = [Document(page_content="doc1")]
    mock_hot_repo.rerank.return_value = [Document(page_content="doc1")]
    
    service = RetrieverService(mock_hot_repo, mock_cold_repo)
    docs = await service.retrieve([0.1, 0.2], hot=False)
    
    assert len(docs) == 1
    assert docs[0].page_content == "doc1"
    mock_cold_repo.search.assert_called_once()
    mock_hot_repo.rerank.assert_called_once()
    mock_hot_repo.search.assert_not_called()

@pytest.mark.asyncio
async def test_retrieve_hot_path(mock_hot_repo, mock_cold_repo):
    mock_hot_repo.search.return_value = [Document(page_content="doc1")]
    
    service = RetrieverService(mock_hot_repo, mock_cold_repo)
    docs = await service.retrieve([0.1, 0.2], hot=True)
    
    assert len(docs) == 1
    mock_hot_repo.search.assert_called_once()
    mock_cold_repo.search.assert_not_called()

@pytest.mark.asyncio
async def test_retrieve_raises_document_not_found(mock_hot_repo, mock_cold_repo):
    mock_cold_repo.search.return_value = []
    
    service = RetrieverService(mock_hot_repo, mock_cold_repo)
    with pytest.raises(DocumentNotFoundException):
        await service.retrieve([0.1, 0.2], hot=False)
