from langchain_core.prompts import ChatPromptTemplate

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

You have access to the following tools:

- **get_booking** — Retrieve full booking details (flight, passengers,
  seats, ancillaries). Requires both user_id and booking_id.
- **get_user_profile** — Retrieve user profile and preferences (name,
  email, loyalty tier, seat/meal preferences). Requires user_id.
- **get_flight_status** — Retrieve real-time flight status
  (departure/arrival times, gate, delays). Requires flight_number.

Always use the available tools before answering. Do not invent information.
If a tool call fails, inform the user that the information is temporarily unavailable."""

agentic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", AGENTIC_SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
