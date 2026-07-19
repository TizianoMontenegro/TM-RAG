from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnableLambda

from app.core.exceptions import DocumentNotFoundException
from app.pipelines.prompts import crag_prompt, crag_relevance_grader_prompt
from app.services.llm_service import LLMService
from app.services.retriever_service import RetrieverService
from app.utils.text import truncate_context


def build_crag_chain(
    retriever_service: RetrieverService,
    llm_service: LLMService,
    embedding_model,
):
    """Factory function to build the CRAG chain.

    Args:
        retriever_service: Service for retrieving documents.
        llm_service: Service for LLM access.
        embedding_model: NVIDIAEmbeddings instance for query embedding.

    Returns:
        A runnable chain for CRAG pipeline.
    """
    llm = llm_service.get_client()
    json_llm = llm_service.get_json_client()
    relevance_parser = JsonOutputParser()

    async def retrieve_and_grade(query: str) -> dict:
        """Retrieve docs and grade relevance."""
        query_vector = await embedding_model.aembed_query(query)
        docs = await retriever_service.retrieve_cold_only(query_vector, top_k=20)

        relevant_docs = []
        for doc in docs:
            try:
                result = await (crag_relevance_grader_prompt | json_llm | relevance_parser).ainvoke(
                    {"document": doc.page_content, "question": query}
                )
                if result.get("score") == "relevant":
                    relevant_docs.append(doc)
            except Exception:
                continue

        if not relevant_docs:
            # Widen search
            docs = await retriever_service.retrieve_cold_only(query_vector, top_k=40)
            for doc in docs:
                try:
                    result = await (
                        crag_relevance_grader_prompt | json_llm | relevance_parser
                    ).ainvoke({"document": doc.page_content, "question": query})
                    if result.get("score") == "relevant":
                        relevant_docs.append(doc)
                except Exception:
                    continue

        if not relevant_docs:
            raise DocumentNotFoundException()

        raw_context = "\n\n".join(d.page_content for d in relevant_docs)
        return {
            "context": truncate_context(raw_context),
            "question": query,
        }

    async def generate(inputs: dict) -> str:
        """Generate response from context and question."""
        return await (crag_prompt | llm | StrOutputParser()).ainvoke(inputs)

    return RunnableLambda(retrieve_and_grade) | RunnableLambda(generate)
