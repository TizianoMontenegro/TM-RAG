from langchain.agents import create_agent
from langchain.tools import tool

from app.core.config import settings
from app.core.exceptions import AgentException
from app.pipelines.prompts import AGENTIC_SYSTEM_PROMPT
from app.services.llm_service import LLMService


@tool
async def get_booking(user_id: str, booking_id: str) -> dict:
    """Retrieve booking details for a given user and booking ID from TM-Backend."""
    import httpx

    try:
        headers = {"Authorization": f"Bearer {settings.tm_rag_api_key.get_secret_value()}"}
        async with httpx.AsyncClient(base_url=settings.backend_api_url, headers=headers) as client:
            response = await client.get(
                f"/api/v1/bookings/{booking_id}/", params={"user_id": user_id}
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
    import httpx

    try:
        headers = {"Authorization": f"Bearer {settings.tm_rag_api_key.get_secret_value()}"}
        async with httpx.AsyncClient(base_url=settings.backend_api_url, headers=headers) as client:
            response = await client.get(f"/api/v1/users/{user_id}/profile/")
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
    import httpx

    try:
        headers = {"Authorization": f"Bearer {settings.tm_rag_api_key.get_secret_value()}"}
        async with httpx.AsyncClient(base_url=settings.backend_api_url, headers=headers) as client:
            response = await client.get(f"/api/v1/flights/{flight_number}/status/")
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
    """
    llm = llm_service.get_client()
    tools = [get_booking, get_user_profile, get_flight_status]
    return create_agent(llm, tools, system_prompt=AGENTIC_SYSTEM_PROMPT)
