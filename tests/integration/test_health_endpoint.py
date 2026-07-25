from unittest.mock import AsyncMock

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


@pytest.mark.asyncio
async def test_readiness_returns_200_when_all_ok(async_client, mocker):
    mocker.patch(
        "app.api.v1.routes.health.check_pgvector", new_callable=AsyncMock, return_value="ok"
    )
    mocker.patch("app.api.v1.routes.health.check_nvidia", new_callable=AsyncMock, return_value="ok")

    response = await async_client.get("/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["pgvector"] == "ok"
    assert data["checks"]["nvidia"] == "ok"


@pytest.mark.asyncio
async def test_readiness_returns_503_when_degraded(async_client, mocker):
    mocker.patch(
        "app.api.v1.routes.health.check_pgvector", new_callable=AsyncMock, return_value="ok"
    )
    mocker.patch(
        "app.api.v1.routes.health.check_nvidia",
        new_callable=AsyncMock,
        return_value="unavailable",
    )

    response = await async_client.get("/v1/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["pgvector"] == "ok"
    assert data["checks"]["nvidia"] == "unavailable"


@pytest.mark.asyncio
async def test_readiness_includes_request_id(async_client, mocker):
    mocker.patch(
        "app.api.v1.routes.health.check_pgvector", new_callable=AsyncMock, return_value="ok"
    )
    mocker.patch("app.api.v1.routes.health.check_nvidia", new_callable=AsyncMock, return_value="ok")

    response = await async_client.get("/v1/health/ready")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.json()["request_id"]
