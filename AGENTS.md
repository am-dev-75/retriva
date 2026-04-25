# Agent Instructions — User-Provided Metadata (v1)

## Mission
Add **user-provided metadata support** to `ingestion_api_v1` in Retriva OSS.

This feature allows ingestion clients (e.g. thin adapter, CLI) to attach arbitrary
user-defined key/value metadata to documents at ingestion time.

The ingestion API v1 must:
- accept user-provided metadata as an optional field
- persist it at document level
- propagate it to all chunks
- expose it for retrieval, filtering, citations, and deletion

## Order of authority
1. `specs/014-user-metadata-ingestion-v1/spec.md`
2. `specs/014-user-metadata-ingestion-v1/architecture.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/014-user-metadata-ingestion-v1/tasks.md`

## Non-negotiable rules
- Do not break existing ingestion_api_v1 clients
- Metadata is opaque to v1 (no routing or interpretation)
- Metadata must be propagated to chunks
- No Open WebUI changes are allowed
