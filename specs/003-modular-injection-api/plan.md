# Plan — Modular Injection API

## Phase 1: Setup API Foundation
1. Integrate FastAPI and Uvicorn into `requirements.txt` (if not already present). Wait, `pydantic` is used, so FastAPI feels natural.
2. Create the `api` module under `src/retriva/api`.
3. Set up the main FastAPI application instance in a new `src/retriva/main.py`.

## Phase 2: Create DTOs and Schemas
1. Create `src/retriva/api/schemas.py` to hold the Pydantic models defining `HtmlIngestRequest`, `TextIngestRequest` and `ChunkIngestRequest`.
2. Ensure they map well to the existing domain models like `ParsedDocument` and `Chunk`.

## Phase 3: Implement Injection Routes
1. Create `src/retriva/api/routers/ingest.py`.
2. Implement `POST /api/v1/ingest/html` utilizing `retriva.ingestion.html_parser` and `chunker`.
3. Implement `POST /api/v1/ingest/text` utilizing `retriva.ingestion.chunker`.
4. Implement `POST /api/v1/ingest/chunks` to push directly to Qdrant.

## Phase 4: Integration
1. Tie the routers into `src/retriva/main.py`.
2. Add a new CLI command to start the API web server in `cli.py` (e.g., `retriva api`).
