# TM Airlines RAG Service

Retrieval-Augmented Generation (RAG) service that processes user queries about TM Airlines using LLM models from NVIDIA AI Endpoints.

## Overview

TM Airlines RAG Service is a FastAPI-based application that:
1. Receives user queries from TM Airlines Backend
2. Retrieves relevant documents from a vector store (pgvector)
3. Generates context-aware responses using NVIDIA AI Endpoints LLM

## Tech Stack

- **Framework**: FastAPI
- **LLM Integration**: LangChain + NVIDIA AI Endpoints
- **Vector Store**: PostgreSQL with pgvector extension
- **Package Manager**: uv
- **Python**: 3.12+

## Status

### Implemented

- [x] FastAPI application setup with lifespan handler
- [x] Configuration management via pydantic-settings
- [x] Structured logging (JSON/text formats)
- [x] Request ID middleware
- [x] Domain exception classes
- [x] Basic exception handling and HTTP status mapping

### Not Yet Implemented

- [ ] Chat endpoint (`/api/v1/chat`)
- [ ] Health endpoint (`/api/v1/health`)
- [ ] RAG service (`app/services/rag_service.py`)
- [ ] LLM service (`app/services/llm_service.py`)
- [ ] Retriever service (`app/services/retriever_service.py`)
- [ ] RAG pipeline (`app/pipelines/rag_pipeline.py`)
- [ ] Prompt templates (`app/pipelines/prompts.py`)
- [ ] Pydantic models (`app/models/chat.py`, `app/models/common.py`)
- [ ] Test fixtures (`tests/conftest.py`)
- [ ] Unit tests
- [ ] Integration tests

## Prerequisites

- Python 3.12 or higher
- NVIDIA API key (sign up at https://build.nvidia.com/)
- PostgreSQL 15+ with pgvector extension

## Installation

```bash
uv sync
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `TM Airlines RAG Service` |
| `APP_VERSION` | Application version | `0.1.0` |
| `DEBUG` | Enable debug mode | `false` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["*"]` |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `PGVECTOR_COLLECTION_NAME` | Vector store collection | `tm_airlines_docs` |
| `NVIDIA_API_KEY` | NVIDIA API key | Required |
| `NVIDIA_BASE_URL` | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_LLM_MODEL` | LLM model name | `meta/llama-3.1-70b-instruct` |
| `NVIDIA_EMBEDDING_MODEL` | Embedding model name | `nvidia/nv-embedqa-e5-v5` |
| `NVIDIA_MAX_TOKENS` | Max tokens for generation | `1024` |
| `NVIDIA_TEMPERATURE` | LLM temperature (0.0-1.0) | `0.2` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (`json` or `text`) | `text` |

## Running the Service

Development:

```bash
uv run python -m uvicorn main:app --reload
```

Production:

```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

_Coming soon..._

Currently, the application starts but has no routes configured.

## Testing

```bash
uv run pytest
```

## Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Project Structure

```
TM-RAG/
├── main.py                 # FastAPI app entry point
├── pyproject.toml         # Project metadata & dependencies
├── uv.lock               # Locked dependencies
├── .env                  # Environment variables
│
├── app/
│   ├── __init__.py
│   ├── api/               # API route handlers
│   │   ├── __init__.py
│   │   ├── deps.py        # Dependency injection
│   │   ├── middleware.py # RequestIDMiddleware
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── chat.py   # TODO: Implement
│   │           └── health.py # TODO: Implement
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py     # Settings (pydantic-settings)
│   │   ├── logging.py    # Structured logging
│   │   └── exceptions.py # Domain exceptions
│   │
│   ├── models/           # Pydantic models
│   │   ├── __init__.py
│   │   ├── chat.py      # TODO: Implement
│   │   └── common.py   # TODO: Implement
│   │
│   ├── pipelines/       # LangChain pipelines
│   │   ├── __init__.py
│   │   ├── prompts.py    # TODO: Implement
│   │   └── rag_pipeline.py # TODO: Implement
│   │
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── rag_service.py     # TODO: Implement
│   │   ├── llm_service.py    # TODO: Implement
│   │   └── retriever_service.py # TODO: Implement
│   │
│   └── utils/
│       ├── __init__.py
│       └── text.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py        # TODO: Implement
    ├── unit/
    │   ├── __init__.py
    │   ├── test_rag_service.py      # TODO: Implement
    │   ├── test_llm_service.py    # TODO: Implement
    │   └── test_retriever_service.py # TODO: Implement
    │
    └── integration/
        ├── __init__.py
        └── test_chat_endpoint.py # TODO: Implement
```

## License

Proprietary - TM Airlines