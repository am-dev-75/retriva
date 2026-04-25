# Feature Spec — User-Provided Metadata (v1)

## Goal
Enable ingestion_api_v1 to accept, persist, and propagate user-provided metadata
supplied at ingestion time.

## In scope
- optional `user_metadata` field in ingestion requests
- validation of metadata shape (string key/value)
- persistence at document level
- propagation to all chunks

## Out of scope
- metadata interpretation
- routing or policy logic
- changes to ingestion API v2

## Functional requirements

### FR1 — Optional metadata acceptance
Ingestion endpoints shall accept an optional `user_metadata` object.

### FR2 — Backward compatibility
Existing clients not providing metadata shall continue to work unchanged.

### FR3 — Document persistence
User metadata shall be stored on the document resource.

### FR4 — Chunk propagation
User metadata shall be copied to every chunk produced from the document.

### FR5 — Retrieval visibility
Metadata shall be available for retrieval filtering and citations.

## Acceptance summary
The feature is accepted when metadata provided at ingestion time is visible on all
chunks and usable by downstream systems.
