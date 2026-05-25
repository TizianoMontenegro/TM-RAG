import logging

from app.core.exceptions import IntentClassificationException
from app.core.logging import request_id_ctx_var
from app.models.chat import ChatRequest, ChatResponse
from app.services.intent_classifier import IntentClassifier
from app.services.llm_service import LLMService
from app.services.retriever_service import RetrieverService
from app.utils.text import clean_query

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        retriever: RetrieverService,
        llm: LLMService,
        intent_classifier: IntentClassifier,
        embedding_model=None,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.intent_classifier = intent_classifier
        self.embedding_model = embedding_model

    async def answer(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a response.

        Args:
            request: The chat request containing query and user info.

        Returns:
            ChatResponse with generated response and metadata.

        Raises:
            IntentClassificationException: If intent classification fails (defaults to policy).
            Other exceptions bubble up to route handler.
        """
        query = clean_query(request.query)
        try:
            intent = await self.intent_classifier.classify(query)
        except IntentClassificationException:
            logger.warning("Intent classification failed — defaulting to policy pipeline")
            intent = "policy"

        if intent == "user_data":
            return await self._run_agentic_pipeline(request, query)
        return await self._run_crag_pipeline(request, query)

    async def _run_crag_pipeline(self, request: ChatRequest, query: str) -> ChatResponse:
        """Run CRAG pipeline for policy queries.

        Args:
            request: The original chat request.
            query: Cleaned query string.

        Returns:
            ChatResponse with generated response.
        """
        from app.pipelines.crag_pipeline import build_crag_chain

        chain = build_crag_chain(self.retriever, self.llm, self.embedding_model)
        response_text = await chain.ainvoke(query)

        return ChatResponse(
            response=response_text,
            conversation_id=request.conversation_id or "",
            sources=None,
            request_id=request_id_ctx_var.get(),
        )

    async def _run_agentic_pipeline(self, request: ChatRequest, query: str) -> ChatResponse:
        """Run agentic pipeline for user-data queries.

        Args:
            request: The original chat request.
            query: Cleaned query string.

        Returns:
            ChatResponse with generated response.
        """
        from app.pipelines.agentic_pipeline import build_agentic_pipeline

        agent_executor = build_agentic_pipeline(self.llm)
        result = await agent_executor.ainvoke({"input": query, "chat_history": []})

        return ChatResponse(
            response=result.get("output", ""),
            conversation_id=request.conversation_id or "",
            sources=None,
            request_id=request_id_ctx_var.get(),
        )
