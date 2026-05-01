# Software Design Document (SDD)

## Feature
Add DELETE /api/v1/documents/{doc_id} endpoint to Retriva backend.

## Motivation
The Retriva Adapter performs reconciliation and issues DELETE requests for removed OWUI files. The backend currently lacks this endpoint, causing repeated 404 responses. Implementing this endpoint restores API contract symmetry and reduces log noise.

## Scope
- HTTP DELETE endpoint
- Idempotent behavior
- No physical data loss beyond document + embeddings

## API Specification

### Endpoint
DELETE /api/v1/documents/{doc_id}

### Semantics
- If document exists: delete document and related embeddings
- If document does not exist: return 404 or 204 (configurable)

### Responses
- 204 No Content (preferred)
- 404 Not Found (if strict mode enabled)

## Data Model Impact
- documents table
- embeddings table (FK cleanup)

## Pseudocode
```
def delete_document(doc_id):
    doc = db.get(Document, doc_id)
    if not doc:
        raise NotFound
    db.delete(doc)
    db.commit()
```

## Security
- Same auth as GET /documents

## Observability
- Log at INFO when delete succeeds
- Log at DEBUG when doc missing

## Backward Compatibility
Safe. Endpoint was previously unimplemented.

## Rollback Plan
Disable route registration.
