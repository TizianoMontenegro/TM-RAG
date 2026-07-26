import httpx
from langchain.agents import create_agent
from langchain.tools import tool

from app.core.config import settings
from app.core.exceptions import AgentException
from app.pipelines.prompts import AGENTIC_SYSTEM_PROMPT
from app.services.llm_service import LLMService

_backend_client: httpx.AsyncClient | None = None


def get_backend_client() -> httpx.AsyncClient:
    """Return a shared httpx client for TM-Backend API calls.

    Reuses TCP connections across tool invocations and enforces timeouts.
    """
    global _backend_client
    if _backend_client is None:
        _backend_client = httpx.AsyncClient(
            base_url=settings.backend_api_url,
            headers={"Authorization": f"Bearer {settings.tm_rag_api_key.get_secret_value()}"},
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0),
        )
    return _backend_client


@tool
async def get_booking(user_id: str, booking_id: str) -> dict:
    """Retrieve booking details for a given user and booking ID from TM-Backend."""
    try:
        client = get_backend_client()
        response = await client.get(
            f"/api/v1/rag/bookings/{booking_id}/", params={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise AgentException(
            message="Booking information is temporarily unavailable.",
            detail=str(e),
        ) from e


@tool
async def get_user_profile(user_id: str) -> dict:
    """Retrieve user profile and preferences from TM-Backend."""
    try:
        client = get_backend_client()
        response = await client.get(f"/api/v1/rag/users/{user_id}/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise AgentException(
            message="User profile is temporarily unavailable.",
            detail=str(e),
        ) from e


@tool
async def get_flight_status(flight_number: str) -> dict:
    """Retrieve real-time flight status from TM-Backend."""
    try:
        client = get_backend_client()
        response = await client.get(f"/api/v1/rag/flights/{flight_number}/status/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise AgentException(
            message="Flight status is temporarily unavailable.",
            detail=str(e),
        ) from e


def build_agentic_pipeline(llm_service: LLMService) -> object:
    """Factory function to build the agentic pipeline.

    Args:
        llm_service: Service for LLM access.

    Returns:
        A compiled state graph that can be invoked with messages.
        Set recursion_limit via config at invoke time:
        ``graph.ainvoke(input, config={"recursion_limit": 5})``
    """
    llm = llm_service.get_client()
    tools = [get_booking, get_user_profile, get_flight_status]
    return create_agent(llm, tools, system_prompt=AGENTIC_SYSTEM_PROMPT)
