# Architecture — Document Deletion (v1)

## Design Principle
Document deletion must be atomic and idempotent. A single request to delete a document by its unique identifier (`doc_id`) must ensure that all associated data, including vector embeddings and metadata, are purged from the system.

## Constraints
- **Idempotency**: Subsequent DELETE requests for the same `doc_id` must return a successful status (204 No Content) to avoid breaking synchronization loops that rely on eventual consistency.
- **Cascade Delete**: Deleting a document implies the removal of all its constituent chunks from the vector store. The system must use metadata-based filters to ensure precise cleanup.

## Data Flow
Client → ingestion_api → documents_router → QdrantStore → Vector Index

1. **Client** issues `DELETE /api/v1/documents/{doc_id}`.
2. **ingestion_api** routes the request to the `delete_document` handler.
3. **QdrantStore** translates the `doc_id` into a point filter on the `source_path` payload field.
4. **Vector Index (Qdrant)** executes the filtered deletion across all matching points.

## Error Handling
- If the document is not found, the system logs an `INFO` message and returns `204 No Content` to maintain idempotency.
- Transport or database errors are logged as `ERROR` and return `500 Internal Server Error`.

## Observability
- Successful deletions are logged with the `doc_id` for auditability.
- Missing documents are logged as "skipping" to differentiate from active deletions.
