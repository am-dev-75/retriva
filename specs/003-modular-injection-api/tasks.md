# Tasks — Modular Injection API

- [ ] Ensure `fastapi` and `uvicorn` are present in dependencies.
- [ ] Implement Request DTOs in `schemas.py`:
  - `HtmlIngestRequest`
  - `TextIngestRequest`
  - `ChunkIngestRequest`
- [ ] Implement the `POST /api/v1/ingest/html` route.
  - Test HTML extraction.
  - Verify chunking rules are applied.
- [ ] Implement the `POST /api/v1/ingest/text` route.
- [ ] Implement the `POST /api/v1/ingest/chunks` route.
- [ ] Wire routers to the main FastAPI app context.
- [ ] Add the `retriva serve` or `retriva api` command in `cli.py` to start the Uvicorn web server.
- [ ] Write integration test validating complete HTTP ingestion using a small mocked Qdrant store.
