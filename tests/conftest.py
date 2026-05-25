from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from langchain_core.documents import Document

from app.core.config import Settings
from app.repositories.base import VectorStoreRepository


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        app_name="TM-RAG-Test",
        app_version="0.1.0",
        debug=True,
        allowed_origins=["*"],
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        pgvector_collection_name="test_collection",
        nvidia_api_key="test_key",
        nvidia_llm_model="meta/llama3-70b-instruct",
        nvidia_embedding_model="nvidia/nv-embedqa-e5-v5",
        nvidia_temperature=0.0,
        log_level="INFO",
        log_format="text",
        backend_api_url="http://tm-backend-test:8000",
    )


@pytest.fixture
def app(mock_settings: Settings):
    from app.api.deps import get_settings
    from main import app as fastapi_app

    fastapi_app.dependency_overrides[get_settings] = lambda: mock_settings
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_nvidia_client(mocker) -> MagicMock:
    return mocker.MagicMock()


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


class MockRepository(VectorStoreRepository):
    async def search(self, query_vector: list[float], top_k: int) -> list[Document]:
        return [Document(page_content="TM Airlines allows one free checked bag.")]

    async def upsert(self, documents: list[Document]) -> None:
        pass

    async def delete(self, ids: list[str]) -> None:
        pass

    async def rerank(
        self, candidates: list[Document], query_vector: list[float], top_k: int
    ) -> list[Document]:
        return candidates[:top_k]
