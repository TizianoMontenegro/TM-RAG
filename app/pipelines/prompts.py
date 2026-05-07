from langchain.prompts import ChatPromptTemplate

# CRAG pipeline prompts
CRAG_SYSTEM_PROMPT = """You are a helpful assistant for TM Airlines customers.
Answer only based on the provided context. If the context does not contain
enough information, say so clearly. Do not invent information."""

crag_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CRAG_SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

CRAG_RELEVANCE_GRADER_PROMPT = """You are a relevance grader.
Given the following retrieved document and user question, respond ONLY with JSON:
{"score": "relevant"} or {"score": "not_relevant"}.

Document: {document}
Question: {question}"""

crag_relevance_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CRAG_RELEVANCE_GRADER_PROMPT),
    ]
)

# Agentic pipeline prompts
AGENTIC_SYSTEM_PROMPT = """You are a helpful assistant for TM Airlines customers.
You have access to tools that retrieve booking information, user data, and flight status.
Always use the available tools before answering. Do not invent information.
If a tool call fails, inform the user that the information is temporarily unavailable."""

agentic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", AGENTIC_SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
