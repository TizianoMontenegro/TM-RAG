from typing import Literal

from langchain_core.output_parsers import JsonOutputParser

from app.core.exceptions import IntentClassificationException
from app.services.llm_service import LLMService

IntentType = Literal["user_data", "policy"]


class IntentClassifier:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm.get_json_client()
        self._parser = JsonOutputParser()

    async def classify(self, query: str) -> IntentType:
        """Classify query as 'user_data' or 'policy'.

        Returns:
            'user_data' — bookings, reservations, personal data, flight status.
            'policy'    — rules, fares, baggage allowances, legal terms, general information.

        Raises:
            IntentClassificationException: If the LLM response cannot be parsed or is not a valid intent.
        """
        prompt = f"""Classify the following query as 'user_data' or 'policy'.
Return ONLY JSON: {{"intent": "user_data"}} or {{"intent": "policy"}}

Query: {query}

JSON:"""
        try:
            response = await self._llm.ainvoke(prompt)
            result = self._parser.parse(
                response.content if hasattr(response, "content") else response
            )
            intent = result.get("intent")
            if intent not in ("user_data", "policy"):
                raise IntentClassificationException(
                    message="Unable to determine query type.",
                    detail=f"Invalid intent value: {intent}",
                )
            return intent  # type: ignore
        except IntentClassificationException:
            raise
        except Exception as e:
            raise IntentClassificationException(
                message="Unable to determine query type.",
                detail=str(e),
            ) from e
