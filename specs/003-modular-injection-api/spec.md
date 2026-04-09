# Feature Spec — Modular Injection API

## Goal
The goal of the Modular Injection API is to decouple the ingestion logic from the local CLI/filesystem constraints and expose Retriva's data processing pipelines over HTTP. This allows external systems (webhooks, crawlers, live sites) to push documentation directly into the Retriva indexing backend.

## Use Cases
1. **Live Wiki Updates**: Automatically push new pages to Retriva upon save.
2. **External Scrapers**: Inject documents retrieved by dedicated web scrapers without keeping local disk mirrors.
3. **Bring-Your-Own-Chunks**: Inject heavily specialized or pre-chunked documents easily, bypassing the standard chunking algorithms.

## In Scope
- A REST API under `/api/v1/ingest/` implementing Pydantic models derived from `src/retriva/domain/models.py`.
- Three main injection strategies:
  - `html`: Submit raw HTML strings to be cleaned, chunked, and embedded.
  - `text`: Submit plain text strictly for chunking and embedding.
  - `chunks`: Submit fully formed `Chunk` objects directly to Qdrant (bypassing chunking logic entirely).
- Relying on the currently implemented modular ingestion logic (`html_parser.py`, `chunker.py`, `qdrant_store.py`).
- HTTP framework integration (FastAPI).

## Out of Scope
- File uploads via `multipart/form-data` (endpoints receive JSON strings).
- Background task queues (Celery/Redis) are out of scope for now. However, FastAPIs `BackgroundTasks` should be leveraged if the user request payload is large.
- Auth / RBAC endpoints. No authentication is meant for the scope of the PoC injection API.
