# TM Airlines RAG Service

![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.135%2B-009688) ![LangChain](https://img.shields.io/badge/LangChain-1.2%2B-1c3c3c) ![NVIDIA AI Endpoints](https://img.shields.io/badge/NVIDIA_AI_Endpoints-✓-76B900) ![Ruff](https://img.shields.io/badge/Ruff-✓-D7FF64) ![pytest](https://img.shields.io/badge/pytest-✓-0A9EDC)

> A Retrieval-Augmented Generation microservice for TM Airlines — answers customer questions with grounded, context-aware responses powered by NVIDIA AI Endpoints.

---

## Overview

TM RAG is the **intelligence layer** between TM Airlines customers and their data. It takes natural-language questions, figures out what the user needs, and routes them to the right pipeline:

- **Policy & legal queries** → Baggage rules, fare conditions, visa info, terms & conditions → answered from TM-RAG's own vector store (pgvector)
- **Personal & booking queries** → Booking status, seat assignments, check-in eligibility, user preferences → answered by calling TM-Backend's internal API through a tool-calling agent

It was designed as a microservice consumed by the main TM-Backend Django application, with end-to-end request tracing and structured logging built in.

---

## ✨ Key Features

- **Dual-pipeline architecture** — Intent classifier routes queries to CRAG (policy docs) or Agentic (user data) automatically
- **Corrective RAG (CRAG)** — LLM self-evaluates retrieved documents, widens search on low confidence, and only generates when relevance is confirmed
- **Hot/cold vector stores** — pgvector for persistent, broad retrieval; FAISS for in-memory re-ranking of candidates
- **Tool-calling agent** — LangGraph `create_react_agent` with tools for booking, profile, and flight status lookups via TM-Backend API
- **End-to-end tracing** — Every request gets a `X-Request-ID` propagated through logs and responses for full trace correlation
- **Structured logging** — JSON or text format, request-scoped context variables

---

## 🧱 Architecture

```
POST /v1/chat
      |
IntentClassifier
 user_data | policy
      |         |
 Agentic      CRAG
 Pipeline    Pipeline
   |            |
 TM-API    Retrieve
               |
             Grade
               |
          Widen / Gen
               |
        ChatResponse
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.12+
- An [NVIDIA API key](https://build.nvidia.com/)
- PostgreSQL 15+ with the pgvector extension installed
- `uv` package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

**1. Clone and install dependencies**

```bash
uv sync
```

**2. Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and set at minimum `DATABASE_URL` and `NVIDIA_API_KEY`.

**3. Start the dev server**

```bash
uv run python -m uvicorn main:app --reload
```

The API is now at `http://localhost:8000`. Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 📡 API Reference

### `GET /v1/health`

Lightweight health check. No dependencies — always fast.

```bash
curl http://localhost:8000/v1/health
```

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-05-29T12:00:00Z"
}
```

---

### `POST /v1/chat`

Main query endpoint. Send a question and get a grounded response.

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: my-trace-id-123" \
  -d '{
    "query": "What is my checked baggage allowance?",
    "user_id": "usr_abc123",
    "conversation_id": null
  }'
```

```json
{
  "response": "Your fare includes one free checked bag up to 23 kg (50 lb). Additional bags are charged at $75 each.",
  "conversation_id": "",
  "sources": null,
  "request_id": "my-trace-id-123"
}
```

#### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | 1–2000 characters |
| `user_id` | string | yes | Opaque user identifier from TM-Backend |
| `conversation_id` | string or null | no | For future multi-turn support |

#### Response codes

| Code | When | Body |
|------|------|------|
| `200` | Success | `ChatResponse` with generated answer |
| `404` | No relevant documents found | `ErrorResponse` |
| `503` | LLM / NVIDIA API unavailable | `ErrorResponse` |
| `502` | Retriever or Agent failure | `ErrorResponse` |
| `422` | Validation error (empty query, etc.) | FastAPI validation error |
| `500` | Unexpected internal error | `ErrorResponse` |

---

## 🔧 Configuration

All settings are loaded from environment variables or a `.env` file. Copy `.env.example` to `.env` to get started.

### FastAPI

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `TM Airlines RAG Service` | Application title |
| `APP_VERSION` | `0.1.0` | Version shown in health check |
| `DEBUG` | `false` | Enable reload on code changes |
| `ALLOWED_ORIGINS` | `["*"]` | CORS allowed origins (comma-separated) |
| `BACKEND_API_URL` | required | Internal TM-Backend API base URL (for Agentic pipeline) |

### PostgreSQL / pgvector

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | required | PostgreSQL connection string |
| `PGVECTOR_COLLECTION_NAME` | `tm_airlines_docs` | Name of the vector collection |

### NVIDIA AI Endpoints

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | required | Your NVIDIA API key |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | API base URL |
| `NVIDIA_LLM_MODEL` | `meta/llama-3.1-70b-instruct` | Model for response generation |
| `NVIDIA_EMBEDDING_MODEL` | `nvidia/nv-embedqa-e5-v5` | Model for text embeddings |
| `NVIDIA_MAX_TOKENS` | `1024` | Maximum tokens per generation |
| `NVIDIA_TEMPERATURE` | `0.2` | LLM temperature (0.0 – 1.0) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | `text` | Output format: `json` or `text` |

---

## 🚀 Deployment

### Production server

```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Set `DEBUG=false` and `LOG_FORMAT=json` in your `.env` for production.

### Docker (recommended)

A minimal `Dockerfile`:

```dockerfile
FROM python:3.12-slim

RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Make sure your PostgreSQL instance with pgvector is reachable from the container.

### Environment checklist for production

- [ ] `DATABASE_URL` points to a pgvector-enabled PostgreSQL
- [ ] `NVIDIA_API_KEY` is set (use a secret manager, not plaintext)
- [ ] `BACKEND_API_URL` points to the internal TM-Backend service
- [ ] `LOG_FORMAT=json` for log aggregation
- [ ] `ALLOWED_ORIGINS` is restricted to known TM-Backend domains

---

## 🛠️ Troubleshooting

| Problem | Likely cause | Solution |
|---------|-------------|----------|
| App crashes at startup with `ValidationError` | Missing `DATABASE_URL` or `NVIDIA_API_KEY` | Check both are set in `.env` |
| `pgvector extension not found` | PostgreSQL doesn't have pgvector installed | Run `CREATE EXTENSION vector;` in your database |
| Chat returns `503` | NVIDIA API key is invalid or quota exceeded | Verify `NVIDIA_API_KEY` and check your NVIDIA account |
| Agentic pipeline returns `502` | TM-Backend is unreachable | Check that `BACKEND_API_URL` is correct and TM-Backend is running |
| `connection refused` on database | PostgreSQL isn't running or credentials are wrong | Verify `DATABASE_URL` and that the server is accepting connections |
| No relevant documents (404) | Vector store is empty | Run the ingest pipeline to populate documents |
| LLM responses are nonsensical | Temperature is too high or context is truncated | Keep `NVIDIA_TEMPERATURE` between 0.0 and 0.3 |

---

## 🧪 Development

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unit/test_rag_service.py -v

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

---

## 📁 Project Structure

```
TM-RAG/
├── main.py                     # FastAPI app entry point
├── pyproject.toml              # Dependencies & tool config
├── .env.example                # Environment variable template
│
├── app/
│   ├── api/                    # Presentation layer
│   │   ├── deps.py             # Dependency injection
│   │   ├── middleware.py        # Request ID middleware
│   │   └── v1/routes/
│   │       ├── chat.py         # POST /v1/chat
│   │       └── health.py       # GET /v1/health
│   │
│   ├── core/                   # Config, exceptions, logging
│   │   ├── config.py           # Pydantic settings
│   │   ├── exceptions.py       # Domain exception hierarchy
│   │   └── logging.py          # Structured logging
│   │
│   ├── models/                 # Pydantic request/response models
│   │   ├── chat.py
│   │   └── common.py
│   │
│   ├── pipelines/              # LangChain chains & agents
│   │   ├── crag_pipeline.py     # Corrective RAG (policy queries)
│   │   ├── agentic_pipeline.py  # Tool-calling agent (user data)
│   │   ├── ingest_pipeline.py   # Document ingestion
│   │   └── prompts.py           # All prompt templates
│   │
│   ├── repositories/           # Vector store interface & impls
│   │   ├── base.py             # Abstract VectorStoreRepository
│   │   ├── pgvector_repository.py
│   │   └── faiss_repository.py
│   │
│   ├── services/               # Business logic
│   │   ├── rag_service.py      # Orchestrator & router
│   │   ├── llm_service.py      # ChatNVIDIA wrapper
│   │   ├── retriever_service.py
│   │   └── intent_classifier.py
│   │
│   └── utils/
│       └── text.py             # Query cleaning & truncation
│
└── tests/
    ├── conftest.py             # Fixtures & mock repository
    ├── unit/
    │   ├── test_rag_service.py
    │   ├── test_retriever_service.py
    │   ├── test_llm_service.py
    │   ├── test_intent_classifier.py
    │   └── test_text.py
    └── integration/
        ├── test_chat_endpoint.py
        └── test_health_endpoint.py
```
