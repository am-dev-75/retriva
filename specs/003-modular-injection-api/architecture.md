# Architecture — Modular Injection API

## Overview
The Modular Injection API introduces a thin HTTP layer (using FastAPI) to expose the existing domain logic found in `src/retriva/ingestion` and `src/retriva/indexing`.

## Components
1. **API Router (`src/retriva/api/injection.py`)**:
   - Implements FastAPI routes matching `openapi.yaml`.
   - Validates incoming JSON payloads using Pydantic schemas.

2. **Ingestion Pipelines**:
   - `POST /api/v1/ingest/html`: 
     - Calls `html_parser.extract_main_content()`.
     - Maps into a `ParsedDocument`.
     - Calls `chunker.create_chunks()`.
     - Calls `qdrant_store.upsert_chunks()`.
   - `POST /api/v1/ingest/text`:
     - Maps directly to a `ParsedDocument`.
     - Calls `chunker.create_chunks()`.
     - Calls `qdrant_store.upsert_chunks()`.
   - `POST /api/v1/ingest/chunks`:
     - Validates payload against `Chunk` Pydantic models.
     - Calls `qdrant_store.upsert_chunks()`.

## Data Models
The data models mirror `src/retriva/domain/models.py`:
- `ChunkMetadata` and `Chunk` are reused directly.
- The requests representations `HtmlIngestRequest`, `TextIngestRequest`, and `ChunkIngestRequest` act as the data-transfer objects (DTOs).

## Execution Context
For this PoC version, the API may execute chunking and indexing either synchronously or simply leveraging FastAPI's `BackgroundTasks` to free the HTTP thread immediately. Qdrant store interactions are already robust due to batch payload sizes limits and retry logic implemented in `qdrant_store.py`.
