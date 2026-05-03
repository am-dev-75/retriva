# Architecture — Retriva Core API v2 Ingestion Pipeline

## 1. Overview

The v2 ingestion API introduces a **generic, format-agnostic** document ingestion
pipeline that coexists with the existing v1 type-specific endpoints. It unifies
all document formats behind a single entry point, adds a stage-aware job model for
observability, and routes documents to the appropriate parser via MIME detection.

### Design Principles

| Principle | Rationale |
|-----------|-----------|
| **v1 isolation** | Zero modifications to any `/api/v1` route, schema, or import |
| **Single responsibility** | Each pipeline stage is a distinct, testable unit |
| **Registry-driven** | Parser routing uses `CapabilityRegistry` — extensible without code changes |
| **Metadata-first** | `user_metadata` flows through every stage into every chunk |

---

## 2. System Topology

```
                ┌─────────────────────────────────────────────┐
                │           FastAPI Application                │
                │                                             │
                │  ┌───────────────┐   ┌───────────────────┐  │
                │  │ /api/v1/*     │   │ /api/v2/*         │  │
                │  │ (unchanged)   │   │ (new)             │  │
                │  │               │   │                   │  │
                │  │ • ingest/text │   │ • documents       │  │
                │  │ • ingest/html │   │ • documents/upload│  │
                │  │ • ingest/pdf  │   │ • jobs            │  │
                │  │ • ingest/...  │   │                   │  │
                │  │ • jobs        │   │                   │  │
                │  │ • documents   │   │                   │  │
                │  └───────┬───────┘   └────────┬──────────┘  │
                │          │                    │              │
                │          │    ┌───────────┐   │              │
                │          └────┤JobManager ├───┘              │
                │               │(singleton)│                  │
                │               └─────┬─────┘                 │
                │                     │                        │
                │          ┌──────────┴──────────┐             │
                │          │  CapabilityRegistry  │            │
                │          │  • chunker           │            │
                │          │  • parser_router     │  ← NEW     │
                │          │  • html_parser       │            │
                │          │  • pdf_extractor     │            │
                │          └──────────┬───────────┘            │
                │                     │                        │
                │          ┌──────────┴──────────┐             │
                │          │    Qdrant Store      │            │
                │          │  (retriva_chunks)    │            │
                │          └─────────────────────┘             │
                └─────────────────────────────────────────────┘
```

### Router Mounting

`/api/v1` and `/api/v2` are mounted as **separate FastAPI routers** on the same
application instance. They share:
- The same `JobManager` singleton (v2 jobs use stage fields; v1 jobs leave them `None`)
- The same `CapabilityRegistry` (v2 adds `parser_router` capability)
- The same Qdrant collection (`retriva_chunks`)

---

## 3. Data Flow — v2 Pipeline

```
Client ─── POST /api/v2/documents ──► [Endpoint]
                                          │
                                          ▼
                                    ┌──────────┐
                                    │ DETECTING │ ─── MIME detection
                                    └────┬─────┘     (explicit hint > extension)
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │PREPROCESSING │ ─── source validation
                                  └──────┬───────┘     temp file handling
                                         │
                                         ▼
                                    ┌─────────┐
                                    │ PARSING │ ─── ParserRouter dispatches to:
                                    └────┬────┘     • text/plain → read file
                                         │          • text/html → HTMLParser
                                         │          • application/pdf → PdfExtractor
                                         │          • text/markdown → MarkdownParser
                                         │          • (future: Docling, OCRmyPDF)
                                         ▼
                                 ┌───────────────┐
                                 │ NORMALIZATION │ ─── normalize_text()
                                 └───────┬───────┘     whitespace cleanup
                                         │
                                         ▼
                                    ┌──────────┐
                                    │ CHUNKING │ ─── DefaultChunker
                                    └────┬─────┘     recursive split
                                         │           user_metadata propagation
                                         ▼
                                    ┌──────────┐
                                    │ INDEXING │ ─── embed + upsert to Qdrant
                                    └────┬─────┘     batched, cancellable
                                         │
                                         ▼
                                   [Job COMPLETED]
```

### Stage Lifecycle

Each stage transition is recorded via `JobManager.advance_stage(job_id, stage)`:

```
PENDING → RUNNING → DETECTING → PREPROCESSING → PARSING →
                     NORMALIZATION → CHUNKING → INDEXING → COMPLETED
```

On error at any stage, the job transitions to `FAILED` with the failing stage
still set as `current_stage` — providing immediate diagnostic context.

---

## 4. Endpoint Design

### 4.1 JSON Body — `POST /api/v2/documents`

```
Content-Type: application/json

{
  "source_uri": "/data/docs/report.pdf",
  "content_type": "application/pdf",     // optional — overrides detection
  "user_metadata": {"tenant": "A"},      // optional
  "parser_hint": null                    // optional — force parser backend
}

→ 202 Accepted
{
  "status": "accepted",
  "message": "Document accepted",
  "job_id": "abc123..."
}
```

### 4.2 File Upload — `POST /api/v2/documents/upload`

```
Content-Type: multipart/form-data

file:          <binary>
source_path:   "uploaded/report.pdf"     // required
content_type:  "application/pdf"         // optional
user_metadata: '{"tenant": "A"}'         // optional, JSON-encoded string
```

Both endpoints share the same background worker pipeline.

### 4.3 Job Status — `GET /api/v2/jobs/{job_id}`

```json
{
  "job_id": "abc123...",
  "status": "running",
  "source": "/data/docs/report.pdf",
  "job_type": "v2_document",
  "current_stage": "PARSING",
  "stages_completed": ["DETECTING", "PREPROCESSING"],
  "created_at": "2026-05-03T11:30:00Z",
  "updated_at": "2026-05-03T11:30:02Z",
  "error": null
}
```

---

## 5. Component Architecture

### 5.1 ParserRouter

The `ParserRouter` is a new capability registered in the `CapabilityRegistry`
at key `"parser_router"` with default priority 100.

```
         ┌──────────────────────────────────────────┐
         │           DefaultParserRouter             │
         │                                          │
         │  detect_content_type(uri, hint) → MIME   │
         │                                          │
         │  parse(source, MIME) ─┬─► text/plain     │
         │                      ├─► text/html       │
         │                      ├─► application/pdf │
         │                      ├─► text/markdown   │
         │                      └─► fallback (text) │
         └──────────────────────────────────────────┘
                          ▲
                          │ extensions override at priority > 100
                          │
         ┌────────────────┴─────────────────────┐
         │  Future: DoclingParser (priority 200) │
         │  Future: OCRmyPDFParser (priority 150)│
         └──────────────────────────────────────┘
```

**MIME detection order**: explicit `content_type` field → file extension mapping → `application/octet-stream` fallback.

### 5.2 Job Model Extension

The existing `Job` dataclass gains two optional fields:

| Field | Type | Default | Used by |
|-------|------|---------|---------|
| `current_stage` | `Optional[str]` | `None` | v2 only |
| `stages_completed` | `List[str]` | `[]` | v2 only |

v1 jobs never populate these fields. The v1 `JobResponse` schema does not
include them, so v1 API responses are byte-identical to before.

### 5.3 Metadata Flow

```
Request.user_metadata
    │
    ▼
ParsedDocument.user_metadata
    │
    ▼ (Chunker propagates)
ChunkMetadata.user_metadata   ← on every chunk
    │
    ▼ (Qdrant payload)
Point.payload.user_metadata   ← queryable, filterable
```

This reuses the existing v1 metadata propagation path — no new code needed.

---

## 6. Module Map

```
src/retriva/
├── ingestion_api/
│   ├── main.py                  ← MODIFY: register v2 routers
│   ├── schemas.py               ← UNCHANGED (v1)
│   ├── schemas_v2.py            ← NEW: v2 request/response models
│   ├── job_manager.py           ← MODIFY: add stage tracking
│   └── routers/
│       ├── ingest.py            ← UNCHANGED
│       ├── ingest_text.py       ← UNCHANGED
│       ├── ingest_HTML.py       ← UNCHANGED
│       ├── ingest_pdf.py        ← UNCHANGED
│       ├── ingest_mediawiki.py  ← UNCHANGED
│       ├── ingest_markdown.py   ← UNCHANGED
│       ├── ingest_image.py      ← UNCHANGED
│       ├── jobs.py              ← UNCHANGED (v1)
│       ├── documents.py         ← UNCHANGED (v1)
│       ├── v2_documents.py      ← NEW: POST /api/v2/documents[/upload]
│       └── v2_jobs.py           ← NEW: GET /api/v2/jobs
├── ingestion/
│   ├── chunker.py               ← UNCHANGED
│   ├── parser_router.py         ← NEW: MIME detection + dispatch
│   ├── html_parser.py           ← UNCHANGED (consumed by router)
│   ├── pdf_parser.py            ← UNCHANGED (consumed by router)
│   ├── markdown_parser.py       ← UNCHANGED (consumed by router)
│   └── normalize.py             ← UNCHANGED (consumed by pipeline)
└── domain/
    └── models.py                ← UNCHANGED
```

---

## 7. Non-Goals (This Phase)

- No new parser backends (Docling, Unstructured, OCRmyPDF) — stubs only
- No remote URI fetching (HTTP/S3) — source_uri must be a local path
- No async/streaming job progress (WebSocket)
- No v1 route modifications of any kind
