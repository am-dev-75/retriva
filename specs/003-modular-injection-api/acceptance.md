# Acceptance — Modular Injection API

## Automated Criteria
1. **HTML Ingestion**: 
   - Send `POST /api/v1/ingest/html` with an arbitrary but well-formed HTML payload.
   - Verify `202 Accepted` response.
   - Verify that Qdrant receives correctly chunked plaintext of the 'main' portion of the HTML.
2. **Text Ingestion**:
   - Send `POST /api/v1/ingest/text` with arbitrary plaintext.
   - Verify `202 Accepted` response.
   - Verify Qdrant chunks the text exactly matching the character limits configuration.
3. **Chunks Ingestion**:
   - Send `POST /api/v1/ingest/chunks` with arbitrary pre-baked chunks.
   - Verify `202 Accepted` response.
   - Verify chunks reach the Qdrant backend successfully without further modifications.
4. **Error Handling**:
   - Verify bad requests (missing paths, broken schema) yield proper HTTP 422 JSON validation errors or custom HTTP 400 bad requests.

## Integration / Manual Criteria
1. Expose the API server via `retriva api`.
2. Push a document via `curl`.
3. Use the `retriva serve` UI and ask a question about that document to confirm correct full-lifecycle ingestion.
