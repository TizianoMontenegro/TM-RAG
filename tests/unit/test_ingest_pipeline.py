from unittest.mock import AsyncMock

import pytest
from langchain_core.documents import Document

from app.core.exceptions import IngestException
from app.pipelines.ingest_pipeline import run_ingest


@pytest.fixture
def mock_repository(mocker):
    repo = mocker.MagicMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_run_ingest_calls_upsert(mock_repository):
    docs = [
        Document(page_content="TM Airlines baggage policy.", metadata={"source": "policy.pdf"}),
        Document(page_content="Fare conditions.", metadata={"source": "fares.pdf"}),
    ]

    await run_ingest(docs, mock_repository)

    mock_repository.upsert.assert_awaited_once_with(docs)


@pytest.mark.asyncio
async def test_run_ingest_raises_on_failure(mock_repository):
    mock_repository.upsert.side_effect = RuntimeError("DB connection lost")
    docs = [Document(page_content="Some doc.")]

    with pytest.raises(IngestException) as exc_info:
        await run_ingest(docs, mock_repository)

    assert "An error occurred during document ingestion." in str(exc_info.value.message)
