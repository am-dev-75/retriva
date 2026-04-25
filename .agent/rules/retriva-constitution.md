---
description: Constitution for User-Provided Metadata (v1)
alwaysApply: true
---

# Retriva Constitution — User Metadata v1

## Product law
- User-provided metadata is a first-class ingestion concern.
- ingestion_api_v1 stores metadata but does not interpret it.
- Metadata must remain visible to retrieval, filtering, and citations.

## Architecture law
- ingestion_api_v1 remains injector-centric.
- No routing, policy, or parser selection logic is introduced.
- Chunk-level metadata propagation is mandatory.

## Scope law
Out of scope:
- routing rules
- ingestion orchestration
- UI-level metadata editing
- ingestion_api_v2 behavior
