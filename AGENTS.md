# AGENTS.md — TM Airlines RAG Service

> **Purpose**: This file is the single source of truth for every agent, contributor, or AI tool
> working on TM-RAG. It maps the full implementation sequence, marks what is done, defines
> the expected output of each step, and flags open architectural decisions.
>
> **Accuracy contract**: This file must reflect only what is actually implemented.
> If you complete a step, mark it `✅ Done` and update the notes. Do not describe
> pending suggestions or deferred improvements as if they are in the code.

---

## Project Overview

A Retrieval-Augmented Generation (RAG) microservice for TM Airlines, consumed by the Django
backend (TM-Backend). It receives a natural-language query, retrieves relevant documents from a
vector store, and returns a grounded response generated via NVIDIA AI Endpoints.

**Runtime contract with TM-Backend**:
- TM-RAG exposes a REST API. TM-Backend calls it; TM-RAG never calls TM-Backend.
- TM-RAG owns its own PostgreSQL + pgvector instance. It has zero access to the booking database.
- Read-only data (flight schedules, policies) is synced asynchronously from TM-Backend to TM-RAG's store.

---

## Architecture

```
HTTP Request (from TM-Backend)
        ↓
┌──────────────────┐
│   api/           │  Presentation layer  — routing, HTTP validation, middleware
├──────────────────┤
│   services/      │  Business layer      — orchestration, decisions
├──────────────────┤
│   pipelines/     │  Chain layer         — LangChain RAG and ingest chains
├──────────────────┤
│   repositories/  │  Data layer          — abstract vector store interface + implementations
├──────────────────┤
│   pgvector       │  Persistent storage  — source of truth for vectors
│   FAISS          │  In-memory compute   — re-ranking, hot queries
└──────────────────┘
```

**Key patterns**:
- **Layered Architecture** — each layer communicates only with the layer directly below it.
- **Repository Pattern** — `repositories/base.py` defines the abstract `VectorStoreRepository` interface. Services depend on the interface, never on concrete implementations.
- **Dependency Injection** — `api/deps.py` is the single resolution point for all concrete implementations. No other file decides which repository is used.
- **Chain of Responsibility** — LangChain pipelines chain steps: retrieval → prompt → LLM → output parser.

---

## ⚠️ Open Architectural Decision — Repositories Layer

The `repositories/` layer (abstract interface + pgvector/FAISS implementations) and the
`ingest_pipeline.py` are part of the **updated architecture**.

**Open Architectural Decision — ✅ Resolved (Phase 3 Complete)** (Phase 3 Complete)**:
1. ✅ Hot/cold SLA split implemented: FAISS for hot (in-memory, low-latency), pgvector for cold (persistent).
2. ✅ Ingest pipeline scope confirmed — will be implemented in Phase 4 (repositories support `upsert`).
3. ✅ FAISS is in-memory only (no persistence to disk) — acceptable for current deployment target.
4. ✅ `rerank()` method added to `VectorStoreRepository` interface and implemented in `FAISSRepository`.

---

## Tech Stack

| Layer              | Technology                          |
|--------------------|-------------------------------------|
| API Framework      | FastAPI                             |
| LLM Orchestration  | LangChain                           |
| LLM Provider       | NVIDIA AI Endpoints (`ChatNVIDIA`)  |
| Embeddings         | NVIDIA AI Endpoints (`NVIDIAEmbeddings`) |
| Vector Store       | pgvector (PostgreSQL extension)     |
| In-memory Compute  | FAISS                               |
| Settings           | Pydantic `BaseSettings`             |
| Package Manager    | uv                                  |
| Python Version     | 3.12+                               |
| Linting/Formatting | Ruff                                |
| Testing            | pytest + pytest-asyncio             |

---

## Code Style Guidelines

### Formatting
- Use Ruff formatter (Black-compatible)
- Line length: 88 characters (Ruff default)
- Trailing commas: Use where appropriate for readability

### Imports
- Use isort conventions (separate by: stdlib, third-party, local)
- Sort imports alphabetically within each group
- Use explicit relative imports for local modules

### Naming Conventions
- **Functions/Variables**: snake_case (e.g., `get_chat_response`, `user_query`)
- **Classes**: PascalCase (e.g., `ChatRequest`, `RAGService`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_TOKENS`, `DEFAULT_MODEL`)
- **Files**: snake_case (e.g., `chat_service.py`, `rag_pipeline.py`)

### Type Hints
- **Required** for all function signatures (parameters and return types)
- Use built-in types directly (e.g., `str`, `int`, not `typing.Str`)
- Use `Optional` for nullable types: `def func(x: Optional[str] = None) -> Optional[list[str]]:`
- Use `Union` for multiple types: `Union[str, int]`

### Docstrings
- Use Google-style docstrings
- Include: Description, Args, Returns, Raises
```python
def process_query(query: str, context: list[str]) -> str:
    """Process a user query with RAG context.

    Args:
        query: The user's question about TM Airlines.
        context: Retrieved documents for context.

    Returns:
        Generated response from the LLM.

    Raises:
        ValueError: If query is empty or context is invalid.
    """
```

### Error Handling
- Use specific exception types (avoid bare `except:`)
- Domain exceptions defined in `app.core.exceptions` are mapped to HTTP status codes in `main.py`
- Log errors with appropriate severity levels
- Handle NVIDIA API errors gracefully with fallback responses

### HTTP Exception Mapping
All domain exceptions inherit from `RAGServiceException` and are registered in `main.py`:

```python
EXCEPTION_STATUS_MAP = {
    DocumentNotFoundException: 404,
    LLMUnavailableException: 503,
    RetrieverException: 502,
    IngestException: 500,
}
```

- HTTP status codes live in `main.py`, not in the domain layer
- The domain layer (`app.core.exceptions`) is HTTP-agnostic

### Async Operations
- Prefer `async/await` for I/O-bound operations
- Use `httpx.AsyncClient` for async HTTP requests
- Mark route handlers with `async def` when performing async operations

### Constants
- Define configuration constants in a `config.py` or `constants.py`
- Use environment variables for sensitive data (API keys, endpoints)
- Use Pydantic `BaseSettings` for configuration management

---

## Progress Overview

| Phase | Description                     | Status         |
|-------|---------------------------------|----------------|
| 0     | Project Foundation              | ✅ Done        |
| 1     | Core Infrastructure             | ✅ Done        |
| 2     | API Layer                       | ✅ Done        |
| 3     | Data Layer (Repositories)       | ✅ Done        |
| 4     | LangChain Pipelines             | 🔲 Pending     |
| 5     | Services                        | 🔲 Pending     |
| 6     | Utilities                       | 🔲 Pending     |
| 7     | Testing                         | 🔲 Pending     |
| 8     | Linting, Formatting & CI Checks | 🔲 Pending     |

---

## Phase 0 — Project Foundation ⚠️ Mostly Done

### 0.1 — Directory structure ✅ Done

Full folder tree created with all `__init__.py` files and empty module stubs:

```
TM-RAG/
├── app/
│   ├── api/v1/routes/
│   ├── models/
│   ├── services/
│   ├── pipelines/
│   ├── repositories/          # Added in updated architecture
│   ├── core/
│   └── utils/
├── tests/unit/
├── tests/integration/
├── main.py
└── pyproject.toml
```

### 0.2 — `.env.example` ✅ Done

Template with all required environment variable keys, no secret values. Groups:
- FastAPI: `APP_NAME`, `APP_VERSION`, `DEBUG`, `ALLOWED_ORIGINS`
- PostgreSQL: `DATABASE_URL`, `PGVECTOR_COLLECTION_NAME`
- NVIDIA: `NVIDIA_API_KEY`, `NVIDIA_LLM_MODEL`, `NVIDIA_EMBEDDING_MODEL`, `NVIDIA_TEMPERATURE`
- Logging: `LOG_LEVEL`, `LOG_FORMAT`

### 0.3 — `.gitignore` ✅ Done

Excludes `.env`, `__pycache__/`, `.venv/`, `*.pyc`, FAISS index files, and test artifacts.

### 0.4 — Dependencies ✅ Done

All required packages have been added via `uv add`. Verified `pyproject.toml` and `uv.lock` are updated.

```bash
uv add fastapi uvicorn pydantic-settings
uv add langchain langchain-nvidia-ai-endpoints langchain-community
uv add pgvector psycopg2-binary sqlalchemy
uv add faiss-cpu
uv add httpx

uv add --dev pytest pytest-asyncio ruff
```

Note: `httpx` is included only in main dependencies (not duplicated in dev).

---

## Phase 1 — Core Infrastructure ✅ Done

### 1.1 — `app/core/config.py` ✅ Done

**Pattern**: Pydantic `BaseSettings` with `.env` file loading.

**Key implementation decisions**:
- `NVIDIA_API_KEY` and `DATABASE_URL` have **no defaults** — the app raises a `ValidationError`
  at startup if they are missing. This is intentional: fail loudly rather than silently at runtime.
- `settings = Settings()` is instantiated once at module level and imported across all other modules.
  No other file should instantiate `Settings()`.
- `ALLOWED_ORIGINS` is a `list[str]` parsed from a comma-separated env var.
- `APP_VERSION` has a default of `"0.1.0"` — it is not a secret and does not require env override
  in normal operation, but can be overridden via the environment variable `APP_VERSION`.

**Public API**:
```python
from app.core.config import settings

# FastAPI
settings.app_name             # str
settings.app_version          # str  — default "0.1.0"
settings.debug                # bool
settings.allowed_origins      # list[str]

# PostgreSQL
settings.database_url         # str  — no default, fails at startup if missing
settings.pgvector_collection_name  # str

# NVIDIA
settings.nvidia_api_key       # SecretStr — no default, fails at startup if missing
settings.nvidia_llm_model     # str
settings.nvidia_embedding_model    # str
settings.nvidia_temperature   # float

# Logging
settings.log_level            # str
settings.log_format           # str ("json" | "text")
```

**Known pending suggestions** (not yet implemented — do not describe as done):
- `Literal["DEBUG", "INFO", "WARNING", "ERROR"]` type constraint on `log_level`
- `Literal["json", "text"]` type constraint on `log_format`
- `Field(ge=0.0, le=1.0)` validator on `nvidia_temperature`

### 1.2 — `app/core/exceptions.py` ✅ Done

**Pattern**: Custom exception hierarchy with user-facing / internal message split.

**Class hierarchy**:
```
RAGServiceException (base)
├── LLMUnavailableException    — NVIDIA API unreachable or returning errors
├── RetrieverException         — pgvector or FAISS failure
├── DocumentNotFoundException  — retrieval returned zero results
└── IngestException            — document ingestion pipeline failure
```

**Key design**:
- Every exception carries two fields: `message` (user-facing, safe to expose in API responses)
  and `detail` (internal, for logs only — never serialized to the client).
- All service and pipeline layers raise from this hierarchy; route handlers catch and translate
  to HTTP responses.

### 1.3 — `app/core/logging.py` ✅ Done

**Pattern**: `ContextVar`-based request ID propagation + structured logging.

**Key implementation decisions**:
- `_request_id_ctx: ContextVar[str]` carries the current request ID through the async call stack
  without passing it explicitly as a function argument.
- `RequestIDFilter` reads from the `ContextVar` and injects `request_id` into every `LogRecord`.
- `JSONFormatter` serializes records to JSON for production (`LOG_FORMAT=json`).
- Plain text formatter is used for development (`LOG_FORMAT=text`).
- Log level is driven by `settings.log_level`.

**Public API**:
```python
from app.core.logging import setup_logging, get_logger, set_request_id, get_request_id

setup_logging()                          # Call once at app startup
logger = get_logger(__name__)            # Module-level logger
set_request_id("abc-123")               # Set for current async context
current_id = get_request_id()           # Read from current async context
```

**Known pending suggestion** (not yet implemented):
- Move `setup_logging()` call into the FastAPI lifespan handler in `main.py` (Step 2.6).

### 1.4 — `app/api/middleware.py` ✅ Done

**Pattern**: Starlette `BaseHTTPMiddleware` for request ID lifecycle management.

**Key implementation decisions**:
- `RequestIDMiddleware` runs before any route handler.
- Checks for an incoming `X-Request-ID` header; uses it if present, generates a new `uuid4` if not.
  This enables end-to-end trace correlation across TM-Backend → TM-RAG.
- Calls `set_request_id()` from `app.core.logging` to bind the ID to the current async context.
- Injects `X-Request-ID` into the response headers so the caller can correlate.

**Note**: Middleware lives in `app/api/middleware.py`, not in `app/core/`. Core is for
configuration, exceptions, and logging primitives only.

---

## Phase 2 — API Layer ✅ Done

### 2.1 — `app/models/common.py` ✅ Done

**Pattern**: Pydantic v2 `BaseModel` for shared response shapes.

**Models to implement**:

```python
class HealthResponse(BaseModel):
    status: str           # "ok"
    version: str          # from settings.app_version
    timestamp: datetime   # UTC now

class ErrorResponse(BaseModel):
    error: str            # user-facing message (from exception.message)
    request_id: str       # from X-Request-ID context
```

`ErrorResponse` must never include `exception.detail` — that stays in logs only.

### 2.2 — `app/models/chat.py` ✅ Done

**Pattern**: Pydantic v2 `BaseModel` with input validation.

**Models to implement**:

```python
class ChatRequest(BaseModel):
    query: str                             # user's natural-language question
    user_id: str                           # opaque identifier from TM-Backend
    conversation_id: str | None = None    # optional; enables stateful multi-turn

class Source(BaseModel):
    document_id: str
    excerpt: str
    relevance_score: float

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: list[Source] | None = None   # optional; include when retrieval sources are available
    request_id: str
```

**Validation rules**:
- `query`: `min_length=1`, `max_length=2000` — reject empty strings and very long inputs upstream.
- `user_id`: non-empty string.

### 2.3 — `app/api/v1/routes/health.py` ✅ Done

**Pattern**: Simple FastAPI route, no service dependency required.

```python
GET /v1/health
→ 200 HealthResponse
```

**Implementation notes**:
- No authentication required.
- Should remain fast and dependency-free — do not call the database or LLM here.
- Include `APIRouter` with `prefix="/v1"` and `tags=["health"]`.

### 2.4 — `app/api/v1/routes/chat.py` ✅ Done

**Pattern**: FastAPI route with injected `RAGService` via `Depends()`.

```python
POST /v1/chat
Body: ChatRequest
→ 200 ChatResponse
→ 503 ErrorResponse  (LLMUnavailableException)
→ 404 ErrorResponse  (DocumentNotFoundException)
→ 500 ErrorResponse  (RAGServiceException catch-all)
```

**Implementation notes**:
- Route handler catches exceptions from the custom hierarchy and maps them to HTTP status codes.
- `RAGService` is injected via `Depends(get_rag_service)` — route handler has zero business logic.
- At this stage (before the pipeline is wired), return a `ChatResponse` placeholder. Mark with
  a `# TODO: wire RAGService` comment.
- Log all exceptions at `ERROR` level with `logger.exception()` — this captures the full traceback
  in the structured log without exposing it to the client.

### 2.5 — `app/api/deps.py` ✅ Done

**Pattern**: Single resolution point for all `Depends()` functions. No other file decides which
concrete implementation is used.

**Functions to implement**:

```python
def get_settings() -> Settings:
    return settings

def get_hot_repository() -> VectorStoreRepository:
    # Returns FAISSRepository — in-memory, low-latency
    ...

def get_cold_repository() -> VectorStoreRepository:
    # Returns PgVectorRepository — persistent, broad candidate retrieval
    ...

def get_retriever_service(
    hot_repo: VectorStoreRepository = Depends(get_hot_repository),
    cold_repo: VectorStoreRepository = Depends(get_cold_repository),
) -> RetrieverService:
    return RetrieverService(hot_repo=hot_repo, cold_repo=cold_repo)

def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    return LLMService(settings=settings)

def get_rag_service(
    retriever: RetrieverService = Depends(get_retriever_service),
    llm: LLMService = Depends(get_llm_service),
) -> RAGService:
    return RAGService(retriever=retriever, llm=llm)
```

**Note**: If the repositories layer decision (⚠️ Phase 3) is not yet confirmed, implement
`get_hot_repository()` and `get_cold_repository()` as stubs that raise `NotImplementedError`.
Do not leave them silently returning `None`.

### 2.6 — `main.py` ✅ Done

**Pattern**: FastAPI application factory with lifespan handler.

**Implementation checklist**:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()           # from app.core.logging
    # Future: initialise DB connection pool here
    yield
    # Future: close DB connection pool here

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
```

**Key decisions**:
- `setup_logging()` is called inside `lifespan`, not at module import time — this makes startup
  order explicit and testable.
- CORS `allow_origins` comes exclusively from `settings.allowed_origins` — never hardcoded.
- `reload=settings.debug` in the `uvicorn.run()` call if a `__main__` block is included.

---

## Phase 3 — Data Layer (Repositories) ✅ Done

> ⚠️ Confirm the open architectural decision before starting this phase.

### 3.1 — `pp/repositories/base.py ✅ Done

**Pattern**: Abstract base class defining the `VectorStoreRepository` contract.

```python
from abc import ABC, abstractmethod
from langchain_core.documents import Document

class VectorStoreRepository(ABC):

    @abstractmethod
    async def search(self, query_vector: list[float], top_k: int) -> list[Document]:
        """Return the top_k most similar documents to query_vector."""
        ...

    @abstractmethod
    async def upsert(self, documents: list[Document]) -> None:
        """Insert or update documents in the store."""
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Remove documents by ID."""
        ...

    @abstractmethod
    async def rerank(
        self, candidates: list[Document], query_vector: list[float], top_k: int
    ) -> list[Document]:
        """Re-rank candidates using query vector.

        For FAISS: builds a temporary index from candidates and searches within it.
        For PgVector: raises RetrieverException (not supported).
        """
        ...
```

**Rules**:
- Services and pipelines import only `VectorStoreRepository`. They must never import
  `PgVectorRepository` or `FAISSRepository` directly.
- `MockRepository` in `tests/` is the only other concrete subclass outside `repositories/`.

### 3.2 — `pp/repositories/pgvector_repository.py ✅ Done

**Role**: Cold store — persistent, source of truth, broad candidate retrieval.

**Key implementation notes**:
- Uses LangChain's `PGVector` integration (`langchain_community.vectorstores.PGVector`).
- Connection string comes from `settings.database_url`.
- Collection name comes from `settings.pgvector_collection_name`.
- `search()` performs a cosine similarity search returning `top_k` candidates.
- `upsert()` uses `add_documents()` from the LangChain `PGVector` interface.
- All methods are `async` — use `asyncpg` or run sync LangChain calls in a thread pool
  (`asyncio.to_thread`) to avoid blocking the event loop.
- Raises `RetrieverException` on connection errors or query failures.

### 3.3 — `pp/repositories/faiss_repository.py ✅ Done

**Role**: Hot store — in-memory, low-latency, re-ranking of pgvector candidates.

**Key implementation notes**:
- Uses LangChain's `FAISS` integration (`langchain_community.vectorstores.FAISS`).
- Index is built in memory at startup or populated lazily on first query — confirm which
  approach is required (startup pre-warming vs lazy init).
- `search()` performs an L2 or inner-product search over the in-memory index.
- `upsert()` adds document vectors to the in-memory index; does **not** persist to disk
  unless `FAISS.save_local()` is explicitly called.
- `delete()` may require index rebuild — document this limitation in code comments.
- Raises `RetrieverException` on index errors.
- **Pending design decision**: cold-path re-ranking requires building a temporary FAISS index
  from pgvector candidates and searching within that subset — this is distinct from a global
  `search()` over the full in-memory index. A dedicated `rerank()` method may be needed.
  Confirm before implementing (see open architectural decision and Phase 5.2).

---

## Phase 4 — LangChain Pipelines 🔲 Pending

### 4.1 — `app/pipelines/prompts.py` 🔲 Pending

**Pattern**: Centralized LangChain `ChatPromptTemplate` definitions. No prompts anywhere else.

**Templates to define**:

```python
RAG_SYSTEM_PROMPT = """You are a helpful assistant for TM Airlines customers.
Answer only based on the provided context. If the context does not contain
enough information, say so clearly. Do not invent information."""

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
```

**Rules**:
- `{context}` and `{question}` are the only template variables.
- Keep prompt tone airline-appropriate: professional, concise, factual.
- Do not include instructions that could expose internal system details.

### 4.2 — `app/pipelines/rag_pipeline.py` 🔲 Pending

**Pattern**: LangChain LCEL (LangChain Expression Language) chain.

**Chain structure**:
```
retriever_runnable | format_docs | rag_prompt | llm | StrOutputParser()
```

**Implementation notes**:
- `retriever_runnable` wraps `RetrieverService.retrieve()` as a LangChain `Runnable`.
- `format_docs` is a pure function: `lambda docs: "\n\n".join(d.page_content for d in docs)`.
- `llm` is the `ChatNVIDIA` instance from `LLMService`.
- The chain is built in a factory function, not at module import time, so that
  `LLMService` and `RetrieverService` can be injected.
- Raises `LLMUnavailableException` or `RetrieverException` on failure — do not swallow
  LangChain exceptions without wrapping them.

### 4.3 — `app/pipelines/ingest_pipeline.py` 🔲 Pending

> ⚠️ Confirm scope with the open architectural decision before implementing.

**Pattern**: Document → Embedding → pgvector store pipeline.

**Responsibilities**:
- Accept a `list[Document]` (LangChain `Document` objects with `page_content` and `metadata`).
- Embed using `NVIDIAEmbeddings` from `langchain-nvidia-ai-endpoints`.
- Write to `PgVectorRepository.upsert()`.
- Raise `IngestException` on any failure.

**Entry point function**:
```python
async def run_ingest(documents: list[Document], repository: VectorStoreRepository) -> None:
    ...
```

---

## Phase 5 — Services 🔲 Pending

### 5.1 — `app/services/llm_service.py` 🔲 Pending

**Pattern**: Thin wrapper around `ChatNVIDIA` that handles errors and exposes a clean interface.

```python
class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._client = ChatNVIDIA(
            model=settings.nvidia_llm_model,
            api_key=settings.nvidia_api_key.get_secret_value(),
            temperature=settings.nvidia_temperature,
        )

    def get_client(self) -> ChatNVIDIA:
        return self._client
```

**Error handling**:
- Wrap any `httpx` or NVIDIA SDK exception in `LLMUnavailableException`.
- Log `detail` (original exception message) before raising — never include it in `message`.

### 5.2 — `app/services/retriever_service.py` 🔲 Pending

**Pattern**: Repository pattern consumer — depends only on `VectorStoreRepository` interface.

```python
class RetrieverService:
    def __init__(
        self,
        hot_repo: VectorStoreRepository,
        cold_repo: VectorStoreRepository,
    ) -> None:
        self.hot_repo = hot_repo
        self.cold_repo = cold_repo

    async def retrieve(
        self, query_vector: list[float], hot: bool = False
    ) -> list[Document]:
        if hot:
            return await self.hot_repo.search(query_vector, top_k=5)

        # Cold path: fetch broad candidates from pgvector, then re-rank
        # within that candidate set via FAISS.
        #
        # ⚠️ Design note: passing candidates to hot_repo.search() does NOT
        # implement re-ranking. A global FAISS search runs over the full
        # in-memory index and ignores the pgvector candidates entirely.
        # Correct re-ranking requires building a temporary FAISS index from
        # the candidate documents and searching within that subset only.
        # This likely requires a dedicated rerank() method on FAISSRepository
        # rather than reusing search().
        #
        # TODO (Phase 3 - resolved): resolve this before implementing — confirm whether
        # FAISSRepository.rerank(candidates, query_vector, top_k) is added
        # to the VectorStoreRepository interface or handled differently.
        candidates = await self.cold_repo.search(query_vector, top_k=20)
        raise NotImplementedError(
            "Cold-path re-ranking is pending resolution of the FAISSRepository "
            "rerank() design decision. See Phase 3 open architectural decision."
        )
```

**Rules**:
- `RetrieverService` never imports `PgVectorRepository` or `FAISSRepository`.
- The `hot` flag is set by `RAGService` based on query classification — not by the route handler.
- Raises `RetrieverException` if either repository raises.
- Raises `DocumentNotFoundException` if the final result list is empty.

### 5.3 — `app/services/rag_service.py` 🔲 Pending

**Pattern**: Main orchestrator — decides retrieval strategy, runs the pipeline, returns a response.

```python
class RAGService:
    def __init__(
        self,
        retriever: RetrieverService,
        llm: LLMService,
    ) -> None:
        self.retriever = retriever
        self.llm = llm

    async def answer(self, request: ChatRequest) -> ChatResponse:
        ...
```

**Responsibilities**:
1. Classify the query to decide `hot=True` or `hot=False` (initially: always `hot=False`).
2. Embed the query using `NVIDIAEmbeddings`.
3. Call `self.retriever.retrieve(query_vector, hot=...)`.
4. Build and invoke the RAG chain from `rag_pipeline.py`.
5. Return a `ChatResponse` with `response`, `conversation_id`, and optional `sources`.

**Error propagation**: Do not catch exceptions here — let them bubble to the route handler.

---

## Phase 6 — Utilities 🔲 Pending

### 6.1 — `app/utils/text.py` 🔲 Pending

**Functions to implement**:

```python
def clean_query(query: str) -> str:
    """Strip leading/trailing whitespace, collapse internal whitespace, remove null bytes."""
    ...

def truncate_context(context: str, max_tokens: int = 3000) -> str:
    """Truncate context string to approximately max_tokens to avoid LLM context overflow.
    Uses character count as a proxy (1 token ≈ 4 chars). Truncates at sentence boundaries
    where possible."""
    ...
```

**Rules**:
- `clean_query()` is called in `RAGService.answer()` before embedding — never pass raw user
  input directly to the LLM.
- `truncate_context()` is called in `rag_pipeline.py`'s `format_docs` step before the prompt.
- Both functions are pure (no I/O, no side effects) — trivial to unit test without mocking.

---

## Phase 7 — Testing 🔲 Pending

### 7.1 — `tests/conftest.py` 🔲 Pending

**Fixtures to define**:

```python
@pytest.fixture
def mock_settings() -> Settings:
    # Override secrets with test-safe values
    ...

@pytest.fixture
def mock_nvidia_client(mocker) -> MagicMock:
    # Patch ChatNVIDIA to return a fixed response string
    ...

@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    # httpx.AsyncClient pointed at the FastAPI test app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class MockRepository(VectorStoreRepository):
    async def search(self, query_vector, top_k):
        return [Document(page_content="TM Airlines allows one free checked bag.")]
    async def upsert(self, documents): pass
    async def delete(self, ids): pass
```

### 7.2 — Unit tests 🔲 Pending

#### `tests/unit/test_rag_service.py`

- `test_answer_returns_chat_response` — mock retriever + mock LLM, assert shape of `ChatResponse`.
- `test_answer_propagates_retriever_exception` — mock retriever raises `RetrieverException`, assert it bubbles.
- `test_answer_propagates_llm_exception` — mock LLM raises `LLMUnavailableException`, assert it bubbles.

#### `tests/unit/test_retriever_service.py`

- `test_retrieve_cold_path` — `MockRepository` returns docs, assert non-empty result.
- `test_retrieve_hot_path` — `hot=True`, assert only `hot_repo.search()` is called.
- `test_retrieve_raises_document_not_found` — `MockRepository.search()` returns `[]`,
  assert `DocumentNotFoundException`.

#### `tests/unit/test_llm_service.py`

- `test_get_client_returns_chat_nvidia` — assert `get_client()` returns a `ChatNVIDIA` instance.
- `test_llm_unavailable_exception_on_api_error` — mock `ChatNVIDIA` to raise `httpx.ConnectError`,
  assert `LLMUnavailableException` is raised.

### 7.3 — Integration tests 🔲 Pending

#### `tests/integration/test_health_endpoint.py`

- `test_health_returns_200` — `GET /v1/health` → assert `200` and `status == "ok"`.
- `test_health_includes_request_id_header` — assert `X-Request-ID` is present in response headers.

#### `tests/integration/test_chat_endpoint.py`

- `test_chat_returns_200` — valid `ChatRequest`, mocked `RAGService`, assert `200 ChatResponse`.
- `test_chat_propagates_request_id` — assert response `request_id` matches `X-Request-ID` header.
- `test_chat_returns_503_on_llm_failure` — `RAGService` raises `LLMUnavailableException`, assert `503`.
- `test_chat_returns_404_on_no_documents` — `RAGService` raises `DocumentNotFoundException`, assert `404`.
- `test_chat_rejects_empty_query` — `query=""`, assert `422 Unprocessable Entity`.

---

## Phase 8 — Linting, Formatting & CI Checks 🔲 Pending

Run before every commit. All three must pass with zero errors before any PR is opened.

```bash
# Format first, then lint
uv run ruff format .
uv run ruff check .
uv run pytest
```

**Ruff configuration** (add to `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```

**pytest configuration** (add to `pyproject.toml`):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Commands

```bash
uv sync                                  # Install deps
uv run ruff check .                      # Lint
uv run ruff format .                     # Format
uv run pytest                            # Test (all)
uv run pytest path -v                    # Test (single)
uv run python -m uvicorn main:app        # Dev server
```

- Dev server: `reload=True` when `settings.debug=True`, otherwise `reload=False`

---

## API Conventions

- Follow FastAPI standards for endpoints
- Use Pydantic models for request/response validation
- Return JSON responses with appropriate HTTP status codes
- Use proper HTTP methods: GET (retrieval), POST (create/process)
- Include OpenAPI documentation (auto-generated by FastAPI)

## Development Notes

- Always use `uv run` to execute commands within the virtual environment
- Run `ruff check .` before committing to catch linting issues
- Ensure tests pass before merging changes
- The RAG service receives queries from Backend and returns generated responses
- Handle gracefully when NVIDIA API is unavailable

## Testing Guidelines

- Use pytest as the testing framework
- Test files should be in `tests/` directory
- Name test files as `test_*.py` or `*_test.py`
- Use descriptive test names: `test_should_return_response_for_valid_query`
- Mock external dependencies (NVIDIA API, Backend calls)
- Include both unit tests and integration tests where appropriate

## API Request/Response Patterns

### Request Model Example
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., min_length=1, description="User's question")
    conversation_id: Optional[str] = None
    user_id: str
```

### Response Model Example
```python
class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    conversation_id: str
    sources: list[Source] | None = None
    request_id: str
```

## RAG Service Architecture

- RAGService: Main orchestrator for LangChain pipelines
- Implement retrieval (vector search) and generation (LLM) phases
- Cache embeddings or use efficient retrieval when possible
- Log retrieved context for debugging

---

## Dependency Graph

The following shows the order in which modules depend on each other.
Never import a module from a layer above you (e.g., services must not import from `api/`).

```
config.py ──────────────────────────────────────────┐
exceptions.py ──────────────────────────────────────┤
logging.py ─────────────────────────────────────────┤
middleware.py ──────────────────────────────────────┤
                                                     ↓
models/common.py ──────┐
models/chat.py ────────┤
                        ↓
repositories/base.py ──────────────────────────────┐
repositories/pgvector_repository.py ───────────────┤
repositories/faiss_repository.py ──────────────────┤
                                                    ↓
utils/text.py ─────────────────────────────────────┐
pipelines/prompts.py ──────────────────────────────┤
services/llm_service.py ───────────────────────────┤
services/retriever_service.py ─────────────────────┤ (depends on base.py only)
pipelines/rag_pipeline.py ─────────────────────────┤
pipelines/ingest_pipeline.py ──────────────────────┤
services/rag_service.py ───────────────────────────┘
                                                    ↓
api/deps.py ────────────────────────────────────────┐
api/v1/routes/health.py ────────────────────────────┤
api/v1/routes/chat.py ──────────────────────────────┤
                                                     ↓
main.py (wires everything, imports from all above)
```

---

## Invariants — Do Not Break These

| Rule | Rationale |
|------|-----------|
| `settings = Settings()` is instantiated exactly once | Multiple instantiations break config consistency and fail loudly on import |
| Services never import concrete repositories | Breaking the interface contract couples layers and blocks unit testing |
| `exception.detail` never reaches the client | Leaking internal error detail is a security risk |
| `setup_logging()` is called only in the lifespan handler | Calling it at import time makes startup order unpredictable in tests |
| `X-Request-ID` is always propagated | Required for end-to-end trace correlation across TM-Backend → TM-RAG |
| Cold-path re-ranking must operate on pgvector candidates, not the global FAISS index | A global FAISS search does not constitute re-ranking; confirm FAISSRepository design before implementing Phase 5.2 |
| `AGENTS.md` reflects only implemented code | Describing pending suggestions as done violates the accuracy contract |







