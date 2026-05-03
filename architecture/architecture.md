# Retriva — Architecture Reference

> Version 0.23.0 · Generated from source-code analysis · 2026-05-03

---

- [Retriva — Architecture Reference](#retriva--architecture-reference)
  - [1  System Context](#1--system-context)
  - [2  Deployment Topology](#2--deployment-topology)
  - [3  Process Model](#3--process-model)
    - [3.1  Ingestion API (`retriva.ingestion_api`)](#31--ingestion-api-retrivaingestion_api)
    - [3.2  OpenAI-compatible Chat API (`retriva.openai_api`)](#32--openai-compatible-chat-api-retrivaopenai_api)
    - [3.3  CLI (`retriva.cli`)](#33--cli-retrivacli)
  - [4  Package Map](#4--package-map)
  - [5  Data Flow — Ingestion](#5--data-flow--ingestion)
    - [5.1  JSON Endpoint Flow](#51--json-endpoint-flow)
    - [5.2  File-Upload Endpoint Flow (PDF)](#52--file-upload-endpoint-flow-pdf)
    - [5.3  Injectors](#53--injectors)
  - [6  Data Flow — Retrieval \& Answering](#6--data-flow--retrieval--answering)
    - [6.1  Retrieval Pipeline](#61--retrieval-pipeline)
    - [6.2  Streaming vs Non-Streaming](#62--streaming-vs-non-streaming)
  - [7  Domain Model](#7--domain-model)
    - [7.1  Core Entities](#71--core-entities)
    - [7.2  Entity Relationship](#72--entity-relationship)
  - [8  Extensibility — CapabilityRegistry](#8--extensibility--capabilityregistry)
    - [8.1  Registry Mechanics](#81--registry-mechanics)
    - [8.2  Registered Capabilities](#82--registered-capabilities)
    - [8.3  Protocol Contracts](#83--protocol-contracts)
  - [9  External Dependencies](#9--external-dependencies)
    - [9.1  Infrastructure](#91--infrastructure)
    - [9.2  Model Providers](#92--model-providers)
  - [10  Cross-Cutting Concerns](#10--cross-cutting-concerns)
    - [10.1  Configuration](#101--configuration)
    - [10.2  Job Management](#102--job-management)
    - [10.3  Observability](#103--observability)
    - [10.4  User-Provided Metadata](#104--user-provided-metadata)
    - [10.5  Error Handling \& Resilience](#105--error-handling--resilience)
  - [11  API Surface Summary](#11--api-surface-summary)
    - [11.1  Ingestion API (:8000)](#111--ingestion-api-8000)
    - [11.2  OpenAI Chat API (:8001)](#112--openai-chat-api-8001)
  - [12  Key Design Decisions](#12--key-design-decisions)

---

## 1  System Context

Retriva is a Retrieval-Augmented Generation (RAG) platform composed of independently deployable processes that integrate with an external vector database (Qdrant), remote LLM/embedding providers, and an optional Open WebUI frontend.

```
 ┌──────────────┐     ┌─────────────────┐     ┌───────────────┐
 │  Open WebUI  │────▶│  OWUI Adapter   │────▶│ Retriva Core  │
 │  (frontend)  │     │  (control plane) │     │  (data plane)  │
 └──────────────┘     └─────────────────┘     └───────┬───────┘
                                                      │
                              ┌────────────────────────┼────────────────────┐
                              ▼                        ▼                    ▼
                        ┌──────────┐          ┌──────────────┐    ┌──────────────┐
                        │  Qdrant  │          │ Embedding API │    │   LLM API    │
                        │ (vector) │          │ (OpenRouter)  │    │ (OpenRouter)  │
                        └──────────┘          └──────────────┘    └──────────────┘
```

**Retriva Core** is the subject of this document. The OWUI Adapter is a separate repository.

---

## 2  Deployment Topology

Retriva Core runs as **two independent FastAPI processes** plus an optional Streamlit UI and CLI tooling:

| Process | Default Port | Module | Responsibility |
|---|---|---|---|
| **Ingestion API** | 8000 | `retriva.ingestion_api` | Document processing, chunking, indexing |
| **OpenAI Chat API** | 8001 | `retriva.openai_api` | RAG retrieval, LLM prompting, SSE streaming |
| **Streamlit UI** | 3000 | `retriva.ui` | Built-in chat interface (optional) |
| **CLI** | — | `retriva.cli` | Batch ingestion, reindexing |

Both API processes connect to the same Qdrant collection (`retriva_chunks`) and share the same configuration singleton (`retriva.config.settings`).

---

## 3  Process Model

### 3.1  Ingestion API (`retriva.ingestion_api`)

```
                       FastAPI (uvicorn)
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
         ingest/*       jobs.router   documents.router
         routers
              │
              ▼
      BackgroundTasks   ◀── JobManager (singleton, thread-safe)
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  Chunker  Embeddings  Qdrant upsert
```

- All ingestion endpoints return **202 Accepted** immediately.
- Actual processing runs in FastAPI `BackgroundTasks` (thread pool).
- Each job is tracked by the `JobManager` singleton with cooperative cancellation.

### 3.2  OpenAI-compatible Chat API (`retriva.openai_api`)

```
            POST /v1/chat/completions
                      │
              ┌───────┴────────┐
              ▼                ▼
        non-streaming     streaming (SSE)
              │                │
              ▼                ▼
      ┌───────────────────────────────┐
      │     _retrieve_and_select()     │
      │  Vector Search → Rerank →      │
      │  Hybrid Select → Budget        │
      └───────────────┬───────────────┘
                      ▼
               LLM completion
                      │
              ┌───────┴────────┐
              ▼                ▼
         JSON response    SSE generator
         (with citations)  (with inline
                            citation refs)
```

- CORS enabled for cross-origin Open WebUI access.
- Includes `/v1/models` and `/internal/profiler` endpoints.

### 3.3  CLI (`retriva.cli`)

The CLI is a client of the Ingestion API. It discovers files locally, parses them (for complex formats like PDF, MediaWiki, Markdown), and POSTs to the REST API. It supports four injector modes:

| Mode | Formats | CLI flag |
|---|---|---|
| **Default** | HTML, images, plain text | (none) |
| **MediaWiki** | XML exports + linked assets | `--injector mediawiki_export` |
| **PDF** | PDF files (page-by-page) | `--injector pdf` |
| **Markdown** | .md / .markdown files | `--injector markdown` |

---

## 4  Package Map

```
src/retriva/
├── config.py                 # Pydantic Settings singleton
├── registry.py               # CapabilityRegistry (thread-safe singleton)
├── protocols.py              # Protocol (interface) definitions
├── profiler.py               # Request profiler (ContextVar-scoped)
├── cli.py                    # CLI entry point & injector handlers
│
├── domain/
│   └── models.py             # ParsedDocument, Chunk, ChunkMetadata, ImageContext
│
├── ingestion/                # Content processing (parsers, chunker)
│   ├── chunker.py            # DefaultChunker — recursive text split + images
│   ├── html_parser.py        # DefaultHTMLParser — BeautifulSoup extraction
│   ├── pdf_parser.py         # PDF parsing (delegates to PdfExtractor)
│   ├── markdown_parser.py    # Markdown section extraction
│   ├── mediawiki_export_parser.py  # XML export parser + wikitext → plaintext
│   ├── mediawiki_assets.py   # Asset index for MediaWiki images
│   ├── image_parser.py       # HTML image extraction + VLM enrichment
│   ├── vlm_describer.py      # DefaultVLMDescriber — vision model descriptions
│   ├── discover.py           # File discovery by extension
│   ├── normalize.py          # Text normalization
│   └── mirror.py             # Canonical URL mapping
│
├── indexing/                 # Vector storage
│   ├── embeddings.py         # Embedding API client (retry + fallback)
│   └── qdrant_store.py       # Qdrant CRUD (upsert, search, delete)
│
├── ingestion_api/            # Ingestion REST API process
│   ├── main.py               # FastAPI app + lifespan
│   ├── __main__.py           # uvicorn entrypoint
│   ├── schemas.py            # Pydantic request/response models + validation
│   ├── job_manager.py        # Job lifecycle singleton
│   └── routers/
│       ├── ingest.py         # POST /chunks, DELETE /collection
│       ├── ingest_text.py    # POST /text
│       ├── ingest_HTML.py    # POST /html
│       ├── ingest_pdf.py     # POST /pdf, POST /upload/pdf
│       ├── ingest_image.py   # POST /image
│       ├── ingest_mediawiki.py  # POST /mediawiki
│       ├── ingest_markdown.py   # POST /markdown
│       ├── documents.py      # DELETE /documents/{doc_id}
│       └── jobs.py           # GET/POST /jobs
│
├── openai_api/               # OpenAI-compatible Chat API process
│   ├── main.py               # FastAPI app + lifespan
│   ├── __main__.py           # uvicorn entrypoint
│   ├── schemas.py            # OpenAI-compatible Pydantic schemas
│   └── routers/
│       ├── chat_completions.py  # POST /v1/chat/completions
│       ├── models.py            # GET /v1/models
│       └── internal.py          # GET /internal/profiler
│
├── qa/                       # Question-answering pipeline
│   ├── answerer.py           # Orchestrator (sync, streaming, async)
│   ├── retriever.py          # DefaultRetriever — Qdrant semantic search
│   ├── reranker.py           # DefaultReranker — cross-encoder via /rerank
│   ├── hybrid_selector.py    # DefaultHybridSelector — M+L merge
│   ├── prompting.py          # DefaultPromptBuilder — grounded system prompt
│   └── grounding.py          # Post-generation grounding validation
│
└── ui/                       # Streamlit UI (optional)
```

---

## 5  Data Flow — Ingestion

### 5.1  JSON Endpoint Flow

```
Client ──POST──▶ Router ──BackgroundTask──▶ ParsedDocument ──▶ Chunker ──▶ Embeddings ──▶ Qdrant
                   │                              ▲
                   │                              │
                   └──── user_metadata ───────────┘  (propagated to every chunk)
```

1. **Request validation** — Pydantic schema + `@field_validator` for `user_metadata` hard limits
2. **Background processing** — Router creates a `Job` and schedules a `BackgroundTask`
3. **ParsedDocument** — Router builds domain object with content + metadata
4. **Chunking** — `DefaultChunker` splits text recursively; creates image chunks from VLM descriptions
5. **Embedding** — `get_embeddings()` calls the embedding API with batching, retry, and fallback
6. **Indexing** — `upsert_chunks()` writes `PointStruct` to Qdrant using `metadata.model_dump()`

### 5.2  File-Upload Endpoint Flow (PDF)

```
Client ──multipart POST──▶ /upload/pdf
                              │
                    save to temp file
                              │
                    BackgroundTask
                              │
                    parse_pdf(temp_path)  ── per-page ParsedDocument ── Chunker ── ...
                              │
                    cleanup temp file
```

The `/upload/pdf` endpoint accepts multipart form data (file + JSON-encoded metadata) and delegates to the same chunking/indexing pipeline. This is the path used by the OWUI Adapter for file uploads.

### 5.3  Injectors

Injectors are CLI-side components that bridge format-specific parsing with the Ingestion API:

| Injector | Parsing Location | API Endpoint | Granularity |
|---|---|---|---|
| HTML | CLI reads file; API extracts content | `/ingest/html` | 1 request per file |
| Image | API calls VLM | `/ingest/image` | 1 request per image |
| Text | CLI reads file | `/ingest/text` | 1 request per file |
| PDF | CLI parses pages via `PdfExtractor` | `/ingest/pdf` | 1 request per page |
| MediaWiki | CLI parses XML exports | `/ingest/mediawiki` | 1 request per wiki page |
| Markdown | CLI parses headings/sections | `/ingest/markdown` | 1 request per file |

---

## 6  Data Flow — Retrieval & Answering

### 6.1  Retrieval Pipeline

```
User query
    │
    ▼
┌────────────────────────────┐
│  1. Vector Search           │  Qdrant cosine similarity
│     top_k = 20 (default)    │  DefaultRetriever
└────────────┬───────────────┘
             │ 20 chunks
             ▼
┌────────────────────────────┐
│  2. Candidate Selection     │  RETRIEVAL_RERANK_CANDIDATES = 100
│     (limit reranker input)  │
└────────────┬───────────────┘
             │ up to 100 chunks
             ▼
┌────────────────────────────┐
│  3. Cross-Encoder Rerank    │  Cohere-compatible /rerank API
│     top_n = 30              │  DefaultReranker (batched, retried)
└────────────┬───────────────┘
             │ 30 chunks (scored)
             ▼
┌────────────────────────────┐
│  4. Hybrid Selection        │  DefaultHybridSelector
│     M = 4 (reranked)        │  Two-knob merge:
│     L = 2 (vector recall)   │  precision + recall deduplication
└────────────┬───────────────┘
             │ up to M + L chunks
             ▼
┌────────────────────────────┐
│  5. Context Budgeting       │  _limit_chunks_by_citations()
│     max_citations = 25      │  Per-source char limit: 6000
└────────────┬───────────────┘
             │ ≤ 25 sources
             ▼
┌────────────────────────────┐
│  6. Prompt Building         │  DefaultPromptBuilder
│     Grounded system prompt  │  Source-tagged XML blocks
│     Citation format: [Title]│
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  7. LLM Completion          │  OpenAI-compatible API
│     Streaming or sync       │  Temperature, top_p configurable
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  8. Post-Processing         │
│     Citation refs extraction│  _build_citation_refs()
│     Grounding validation    │  validate_grounding() (sync only)
│     SSE re-chunking         │  MAX_SSE_PAYLOAD = 12KB
└────────────────────────────┘
```

### 6.2  Streaming vs Non-Streaming

| Aspect | Non-Streaming | Streaming (SSE) |
|---|---|---|
| Response type | `ChatCompletionResponse` (JSON) | `StreamingResponse` (SSE) |
| Retrieval | Synchronous thread pool | Async thread pool offload |
| LLM call | `client.chat.completions.create()` | `client.chat.completions.create(stream=True)` |
| Citations | Full metadata in response body | Inline `[N]` markers + final metadata events |
| Grounding | `validate_grounding()` applied | Skipped (needs full answer text) |
| Profiler | Marks phases synchronously | Marks phases asynchronously |

---

## 7  Domain Model

### 7.1  Core Entities

| Entity | Module | Purpose |
|---|---|---|
| `ParsedDocument` | `domain.models` | Intermediate representation of an ingested document |
| `Chunk` | `domain.models` | Indexed unit: text + metadata |
| `ChunkMetadata` | `domain.models` | All metadata fields carried into the vector store |
| `ImageContext` | `domain.models` | Extracted image with alt text, caption, VLM description |
| `Job` | `ingestion_api.job_manager` | Lifecycle-tracked async ingestion job |

### 7.2  Entity Relationship

```
ParsedDocument (1) ──────▶ (N) Chunk
       │                         │
       │                         ▼
       │                    ChunkMetadata
       │                         │
       │                         ├── doc_id, source_path, page_title
       │                         ├── section_path, chunk_id, chunk_index
       │                         ├── chunk_type ("text" | "image")
       │                         ├── language, ingestion_timestamp
       │                         ├── image_path (optional)
       │                         └── user_metadata (optional Dict[str, str])
       │
       └──────▶ (N) ImageContext
                         │
                         ├── src, alt, caption
                         ├── surrounding_text
                         └── vlm_description
```

When a `ParsedDocument` enters the chunker:
1. Text is split recursively (paragraph → sentence → space → hard cut).
2. `user_metadata` from the document is copied to every `ChunkMetadata`.
3. Each image becomes a separate chunk with `chunk_type = "image"`.
4. All chunks are embedded and upserted to Qdrant with `metadata.model_dump()` as the point payload.

---

## 8  Extensibility — CapabilityRegistry

### 8.1  Registry Mechanics

The `CapabilityRegistry` is a **thread-safe singleton** that maps capability names to implementation classes ranked by priority.

```python
# OSS defaults register at priority 100
CapabilityRegistry().register("chunker", DefaultChunker, priority=100)

# Extensions override by registering at priority > 100
CapabilityRegistry().register("chunker", ProChunker, priority=200)
```

- **Resolution**: `get_instance(name)` returns a cached singleton of the highest-priority class.
- **Discovery**: `load_extensions(csv)` imports modules from `RETRIVA_EXTENSIONS` env var and calls their `register(registry)` hook.
- **Invalidation**: New registrations clear the instance cache for that capability.

### 8.2  Registered Capabilities

| Capability Key | Default Implementation | Protocol | Package |
|---|---|---|---|
| `chunker` | `DefaultChunker` | `Chunker` | `ingestion.chunker` |
| `html_parser` | `DefaultHTMLParser` | `HTMLParser` | `ingestion.html_parser` |
| `vlm_describer` | `DefaultVLMDescriber` | `VLMDescriber` | `ingestion.vlm_describer` |
| `pdf_extractor` | `DefaultPdfExtractor` | `PdfExtractor` | `ingestion.pdf_parser` |
| `retriever` | `DefaultRetriever` | `Retriever` | `qa.retriever` |
| `reranker` | `DefaultReranker` | — | `qa.reranker` |
| `hybrid_selector` | `DefaultHybridSelector` | — | `qa.hybrid_selector` |
| `prompt_builder` | `DefaultPromptBuilder` | `PromptBuilder` | `qa.prompting` |

### 8.3  Protocol Contracts

Protocols are defined in `retriva.protocols` using `typing.Protocol` with `@runtime_checkable`:

```python
class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int) -> List[Dict]: ...

class Chunker(Protocol):
    def create_chunks(self, document: ParsedDocument) -> List[Chunk]: ...

class HTMLParser(Protocol):
    def extract_content(self, html: str) -> str | None: ...
    def extract_language(self, html: str) -> str: ...

class VLMDescriber(Protocol):
    def describe(self, image_path: Path) -> str: ...

class PromptBuilder(Protocol):
    def build_prompt(self, question: str, chunks: List[Dict]) -> str: ...

class PdfExtractor(Protocol):
    def extract_pages(self, pdf_path: Path) -> list | None: ...
    def extract_metadata(self, pdf_path: Path) -> dict[str, str]: ...
```

---

## 9  External Dependencies

### 9.1  Infrastructure

| Service | Purpose | Connection |
|---|---|---|
| **Qdrant** | Vector storage, search, filtering | `QDRANT_URL` (default: `http://192.168.1.64:6333`) |

Qdrant stores all chunks in a single collection `retriva_chunks` with cosine similarity vectors.

### 9.2  Model Providers

All model calls use the **OpenAI Python SDK** (or `httpx` for reranking), routed through configurable base URLs:

| Role | Default Provider | Default Model | Config Prefix |
|---|---|---|---|
| **Embeddings** | OpenRouter | `baai/bge-m3` (1024-dim) | `EMBEDDING_*` |
| **Chat / LLM** | OpenRouter | `qwen/qwen-2.5-coder-32b-instruct` | `CHAT_*` |
| **Vision / VLM** | OpenRouter | `google/gemini-2.0-flash-001` | `VISUAL_*` |
| **Reranking** | OpenRouter | `cohere/rerank-v3.5` | `RETRIEVAL_RERANK_*` |

A single `OPENROUTER_OPENAI_API_KEY` can serve as fallback for all provider-specific keys.

---

## 10  Cross-Cutting Concerns

### 10.1  Configuration

`retriva.config.Settings` is a Pydantic `BaseSettings` subclass reading from environment variables and `.env`. Key groups:

- **Infrastructure**: Qdrant URL, storage paths
- **Model**: Embedding, chat, visual, reranker model/URL/key
- **Retrieval tuning**: `retriever_top_k`, rerank candidates/top_n, hybrid M/L
- **Chunking**: `max_chunk_chars`, `chunk_overlap`, `indexing_batch_size`
- **Citation**: `max_citations`, `citation_snippet_size`, `max_metadata_per_citation`
- **Extensions**: `retriva_extensions` (comma-separated module paths)
- **Ports**: `ingestion_api_port`, `openai_api_port`, `ui_port`

### 10.2  Job Management

The `JobManager` is a **thread-safe singleton** tracking ingestion jobs through a state machine:

```
PENDING → RUNNING → COMPLETED
                  → FAILED
                  → CANCELLING → CANCELLED
```

Cancellation is **cooperative**: `cancel_check` callbacks are injected into `upsert_chunks()` and `get_embeddings()` and polled at batch boundaries. A `CancellationError` exception propagates from checkpoints to the background worker.

### 10.3  Observability

| Component | Mechanism |
|---|---|
| **Logging** | Structured logging via `retriva.logger` (module-scoped) |
| **Profiler** | `ContextVar`-scoped `Profiler` tracking phase timestamps per request |
| **Internal endpoints** | `/internal/profiler` exposes recent profiler logs |

The profiler is opt-in (`ENABLE_INTERNAL_PROFILER=true`) and tracks: `request_received`, `retrieval_vector_search_complete`, `retrieval_reranking_complete`, `retrieval_hybrid_selection_complete`, `citations_built`, `first_token_received`.

### 10.4  User-Provided Metadata

User metadata (`Dict[str, str]`) flows through the entire pipeline:

```
Client request → Schema validation → ParsedDocument → Chunk → ChunkMetadata → Qdrant payload → Citations
```

Validation enforces:
- String keys and values only
- Max 20 keys
- Max 256 characters per value
- Max 4096 bytes serialized

### 10.5  Error Handling & Resilience

| Layer | Strategy |
|---|---|
| **Embeddings** | 3 retries with exponential backoff; batch fallback to one-by-one; zero-vector on network unreachable |
| **Qdrant upsert** | 3 retries with exponential backoff |
| **Reranker** | 2 retries; graceful fallback to vector-search order on failure |
| **Job failures** | Captured and stored on the `Job` object; no automatic retry |
| **Document deletion** | Idempotent — returns 204 even if document not found |

---

## 11  API Surface Summary

### 11.1  Ingestion API (:8000)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/ingest/text` | Ingest plain text |
| POST | `/api/v1/ingest/html` | Ingest HTML content |
| POST | `/api/v1/ingest/pdf` | Ingest single PDF page (pre-extracted) |
| POST | `/api/v1/ingest/upload/pdf` | Ingest raw PDF file upload (multipart) |
| POST | `/api/v1/ingest/image` | Ingest image (VLM description) |
| POST | `/api/v1/ingest/mediawiki` | Ingest MediaWiki page |
| POST | `/api/v1/ingest/markdown` | Ingest Markdown document |
| POST | `/api/v1/ingest/chunks` | Ingest raw pre-built chunks |
| DELETE | `/api/v1/ingest/collection` | Clear and reinitialize vector collection |
| DELETE | `/api/v1/documents/{doc_id}` | Delete document and its chunks |
| GET | `/api/v1/jobs` | List recent jobs |
| GET | `/api/v1/jobs/{job_id}` | Get job status |
| POST | `/api/v1/jobs/{job_id}/cancel` | Request job cancellation |

### 11.2  OpenAI Chat API (:8001)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/chat/completions` | Chat completion with RAG (streaming/non-streaming) |
| GET | `/v1/models` | List available models |
| GET | `/internal/profiler` | Recent request profiler logs |

---

## 12  Key Design Decisions

| Decision | Rationale |
|---|---|
| **Two separate API processes** | Decouples ingestion load from query latency; allows independent scaling |
| **BackgroundTasks, not Celery** | Keeps the system simple and self-contained; sufficient for current scale |
| **Single Qdrant collection** | All document types coexist; metadata filtering handles scoping |
| **`model_dump()` as payload** | Pydantic serialization ensures all metadata (including `user_metadata`) is automatically included in Qdrant points |
| **Cooperative cancellation** | Avoids thread interruption hazards; callbacks at batch boundaries |
| **Priority-based registry** | OSS defaults at 100; extensions override without modifying core code |
| **OpenAI-compatible API** | Drop-in compatibility with Open WebUI and any OpenAI client |
| **Injector-centric ingestion** | CLI does format-specific parsing; API endpoints are format-aware but thin |
| **Apache 2.0 licensing** | Enables proprietary extensions via the registry without copyleft obligations |
