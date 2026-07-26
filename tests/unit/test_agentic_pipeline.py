from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AgentException


@pytest.fixture(autouse=True)
def _reset_backend_client():
    """Reset the shared httpx client singleton between tests."""
    import app.pipelines.agentic_pipeline as mod

    mod._backend_client = None
    yield
    mod._backend_client = None


def test_get_backend_client_sets_auth_header(mocker):
    from app.pipelines.agentic_pipeline import get_backend_client

    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.tm_rag_api_key.get_secret_value",
        return_value="test_jwt_123",
    )
    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.backend_api_url",
        new="http://test-backend:8000",
    )

    client = get_backend_client()
    assert client.headers["Authorization"] == "Bearer test_jwt_123"


@pytest.mark.asyncio
async def test_get_booking_calls_correct_url(mocker):
    from app.pipelines.agentic_pipeline import get_booking

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"status": "confirmed"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.get = mock_get

    mocker.patch("app.pipelines.agentic_pipeline.get_backend_client", return_value=mock_client)

    await get_booking.ainvoke({"user_id": "1", "booking_id": "ABC123"})

    mock_get.assert_called_once_with("/api/v1/rag/bookings/ABC123/", params={"user_id": "1"})


@pytest.mark.asyncio
async def test_get_user_profile_calls_correct_url(mocker):
    from app.pipelines.agentic_pipeline import get_user_profile

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"email": "alice@test.com"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.get = mock_get

    mocker.patch("app.pipelines.agentic_pipeline.get_backend_client", return_value=mock_client)

    await get_user_profile.ainvoke({"user_id": "1"})

    mock_get.assert_called_once_with("/api/v1/rag/users/1/")


@pytest.mark.asyncio
async def test_get_flight_status_calls_correct_url(mocker):
    from app.pipelines.agentic_pipeline import get_flight_status

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"status": "scheduled"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.get = mock_get

    mocker.patch("app.pipelines.agentic_pipeline.get_backend_client", return_value=mock_client)

    await get_flight_status.ainvoke({"flight_number": "TM100"})

    mock_get.assert_called_once_with("/api/v1/rag/flights/TM100/status/")


@pytest.mark.asyncio
async def test_get_booking_raises_agent_exception_on_http_error(mocker):
    from app.pipelines.agentic_pipeline import get_booking

    mock_get = AsyncMock(side_effect=__import__("httpx").HTTPError("connection failed"))
    mock_client = AsyncMock()
    mock_client.get = mock_get

    mocker.patch("app.pipelines.agentic_pipeline.get_backend_client", return_value=mock_client)

    with pytest.raises(AgentException) as exc_info:
        await get_booking.ainvoke({"user_id": "1", "booking_id": "ABC123"})

    assert "Booking information is temporarily unavailable." in str(exc_info.value.message)
