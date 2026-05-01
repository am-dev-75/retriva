# Specification — Document Deletion (v1)

## Goal
Provide a reliable and idempotent mechanism for removing documents from the Retriva RAG pipeline.

## API Requirements
- Endpoint: `DELETE /api/v1/documents/{doc_id}`
- Status Codes:
    - `204 No Content`: Successful deletion or document already absent.
    - `401 Unauthorized`: Missing or invalid API key (if enabled).
    - `500 Internal Server Error`: Backend failure.

## Functional Requirements
- **Cleanup**: Must remove all vector points in Qdrant where `source_path` matches the provided `doc_id`.
- **Consistency**: After a successful deletion, the document must no longer be retrievable by any search query.
- **Performance**: Deletion should be handled as an atomic update in Qdrant; if a document has thousands of chunks, the operation must still complete within a reasonable timeout.

## Non-Functional Requirements
- **Logging**: Must log document absence as `INFO` to satisfy adapter observability requirements.
