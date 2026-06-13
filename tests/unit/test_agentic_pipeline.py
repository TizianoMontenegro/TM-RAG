from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AgentException


@pytest.mark.asyncio
async def test_get_booking_sends_service_jwt_header(mocker):
    from app.pipelines.agentic_pipeline import get_booking

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"status": "confirmed"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get = mock_get

    mock_async_client = mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.tm_rag_api_key.get_secret_value",
        return_value="test_jwt_123",
    )

    await get_booking.ainvoke({"user_id": "1", "booking_id": "ABC123"})

    _, kwargs = mock_async_client.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test_jwt_123"


@pytest.mark.asyncio
async def test_get_user_profile_sends_service_jwt_header(mocker):
    from app.pipelines.agentic_pipeline import get_user_profile

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"email": "alice@test.com"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get = mock_get

    mock_async_client = mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.tm_rag_api_key.get_secret_value",
        return_value="test_jwt_456",
    )

    await get_user_profile.ainvoke({"user_id": "1"})

    _, kwargs = mock_async_client.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test_jwt_456"


@pytest.mark.asyncio
async def test_get_flight_status_sends_service_jwt_header_and_v1_url(mocker):
    from app.pipelines.agentic_pipeline import get_flight_status

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"status": "scheduled"})
    mock_get = AsyncMock(return_value=mock_response)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get = mock_get

    mock_async_client = mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.tm_rag_api_key.get_secret_value",
        return_value="test_jwt_789",
    )

    await get_flight_status.ainvoke({"flight_number": "TM100"})

    _, kwargs = mock_async_client.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test_jwt_789"

    # Verify the URL is called correctly via the mocked client.get
    call_url = mock_get.call_args[0][0]
    assert "/api/v1/flights/TM100/status/" in call_url


@pytest.mark.asyncio
async def test_get_booking_raises_agent_exception_on_http_error(mocker):
    from app.pipelines.agentic_pipeline import get_booking

    mock_get = AsyncMock(side_effect=__import__("httpx").HTTPError("connection failed"))
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get = mock_get
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch(
        "app.pipelines.agentic_pipeline.settings.tm_rag_api_key.get_secret_value",
        return_value="test_jwt",
    )

    with pytest.raises(AgentException) as exc_info:
        await get_booking.ainvoke({"user_id": "1", "booking_id": "ABC123"})

    assert "Booking information is temporarily unavailable." in str(exc_info.value.message)
