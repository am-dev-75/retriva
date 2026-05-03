# Implementation Tasks
1. **Scaffolding**: Create `/api/v2` routers and register them alongside `/api/v1`.
2. **Data Models**: Create v2 Pydantic schemas (e.g., `DocumentIngestRequestv2`) and stage-aware `Job` models.
3. **Metadata Propagation**: Ensure `user_metadata` from the request payload is injected into every emitted chunk.
4. **Parser Abstractions**: Define the interface for parser routing (Tika, Docling, Unstructured, OCRmyPDF).
5. **Endpoints**: Implement `POST /api/v2/documents`.
