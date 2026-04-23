# AGENTS.md - TM Airlines RAG Service

## Project Overview

- **Project Name**: TM Airlines RAG (Retrieval-Augmented Generation) Service
- **Python Version**: 3.12+
- **Package Manager**: uv
- **Tech Stack**: FastAPI, LangChain, LangChain NVIDIA AI Endpoints
- **Purpose**: RAG service that communicates with TM Airlines Backend, serves as an API for processing queries using LLM models from NVIDIA AI Endpoints

## Commands

```bash
uv sync                                  # Install deps
uv run ruff check .                      # Lint
uv run ruff format .                     # Format
uv run pytest                         # Test (all)
uv run pytest path -v                  # Test (single)
uv run python -m uvicorn main:app --reload  # Dev server
```

## Architecture

- **Entrypoint**: `main:app` (FastAPI)
- **Config**: `app.core.config.settings` (pydantic-settings, reads `.env`)
- **Logging**: `app.core.logging` — uses standard `logging` library, NOT structlog
  ```python
  from app.core.logging import setup_logging, get_logger
  setup_logging(log_level=settings.log_level, log_format=settings.log_format)
  logger = get_logger(__name__)
  ```
- **Request ID**: Auto-injected via `RequestIDMiddleware`. Access via `request_id_ctx_var`:
  ```python
  from app.core.logging import request_id_ctx_var
  request_id_ctx_var.set("abc-123")
  ```

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
- Return proper HTTP error responses via FastAPI's `HTTPException`
- Log errors with appropriate severity levels
- Handle NVIDIA API errors gracefully with fallback responses

### Async Operations
- Prefer `async/await` for I/O-bound operations
- Use `httpx.AsyncClient` for async HTTP requests
- Mark route handlers with `async def` when performing async operations

### Constants
- Define configuration constants in a `config.py` or `constants.py`
- Use environment variables for sensitive data (API keys, endpoints)
- Use Pydantic `BaseSettings` for configuration management

## Project Structure

```
TM-RAG/
├── main.py                 # FastAPI app entry point
├── pyproject.toml          # Project metadata & dependencies
├── uv.lock                 # Locked dependencies
├── .python-version         # Python version specification
├── .env                    # Environment variables (gitignored)
├── app/                   # Application code
│   ├── __init__.py
│   ├── api/               # API route handlers
│   │   ├── deps.py
│   │   ├── middleware.py  # RequestIDMiddleware ✅
│   │   └── v1/routes/
│   │       ├── chat.py    # [needs implementation]
│   │       └── health.py  # [needs implementation]
│   ├── core/
│   │   ├── config.py      # Settings (pydantic-settings) ✅
│   │   ├── logging.py     # Structured logging (JSON/text) ✅
│   │   └── exceptions.py
│   ├── models/            # Pydantic request/response models
│   │   ├── chat.py        # [needs implementation]
│   │   └── common.py
│   ├── pipelines/         # LangChain pipelines
│   │   ├── prompts.py
│   │   └── rag_pipeline.py
│   ├── services/          # Business logic
│   │   ├── rag_service.py     # [needs implementation]
│   │   ├── llm_service.py
│   │   └── retriever_service.py
│   └── utils/
│       └── text.py
└── tests/
    ├── conftest.py        # [needs implementation]
    ├── unit/
    │   ├── test_rag_service.py      # [needs implementation]
    │   ├── test_llm_service.py       # [needs implementation]
    │   └── test_retriever_service.py # [needs implementation]
    └── integration/
        └── test_chat_endpoint.py    # [needs implementation]
```

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
    sources: Optional[list[str]] = None
```

## RAG Service Architecture

- RAGService: Main orchestrator forLangChain pipelines
- Implement retrieval (vector search) and generation (LLM) phases
- Cache embeddings or use efficient retrieval when possible
- Log retrieved context for debugging