import pytest

@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    response = await async_client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_health_includes_request_id_header(async_client):
    response = await async_client.get("/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
