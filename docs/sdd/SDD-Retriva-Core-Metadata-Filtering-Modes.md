# SDD Pack — Retriva Core Metadata Filtering Modes

## Status
Proposed

## Scope
Retriva Core only.

This SDD modifies Retriva Core to support explicit metadata filtering modes for document discovery and RAG retrieval.

---

## Objective

Implement Core support for:

```text
metadata_filter_mode = soft | hard
```

Where:

```text
soft → metadata is a ranking/recall signal
hard → metadata is a mandatory payload constraint
```

Filters must apply to all supported chunk payload metadata fields, not only `user_metadata`.

---

## Metadata Filter Object

Core must accept filters in this form:

```json
{
  "field": "user_metadata.project",
  "operator": "eq",
  "value": "apollo"
}
```

Required operators:

```text
eq
exists
```

Optional future operators:

```text
neq
contains
in
```

Supported fields are payload fields, including but not limited to:

```text
user_metadata.*
chunk_type
language
source_path
page_title
doc_id
section_path
```

---

## Core APIs

### POST `/api/v2/retrieval/query`

Used by Chat/RAG.

Request:

```json
{
  "query": "What are the costs of the Apollo project?",
  "kb_ids": ["default"],
  "metadata_filters": [
    {
      "field": "user_metadata.project",
      "operator": "eq",
      "value": "apollo"
    }
  ],
  "metadata_filter_mode": "soft",
  "top_k": 20,
  "rerank": true,
  "hybrid_selection": true
}
```

### POST `/api/v2/documents/search`

Used by Documents/Search screen.

Request:

```json
{
  "query": "apollo project",
  "kb_ids": ["default"],
  "metadata_filters": [
    {
      "field": "user_metadata.project",
      "operator": "eq",
      "value": "apollo"
    }
  ],
  "metadata_filter_mode": "hard",
  "limit": 50
}
```

Response must be document-level, deduplicated by `doc_id`.

---

## Hard Mode Semantics

When `metadata_filter_mode=hard`:

- Metadata filters are converted into Qdrant payload `must` filters.
- Vector search only considers matching chunks.
- Reranking only considers matching chunks.
- Hybrid selection must not reintroduce non-matching chunks.
- Document discovery only returns documents with matching chunks.

If no chunks match, Core returns an empty result with a clear status/message.

---

## Soft Mode Semantics

When `metadata_filter_mode=soft`:

- Metadata filters are not exclusion constraints.
- Core uses metadata matches as recall/ranking signals.
- Untagged but semantically relevant documents/chunks may still be returned.

Recommended candidate construction:

```text
semantic candidates
∪ metadata-matching candidates
∪ title/path/document-field candidates
```

Then:

```text
merge → deduplicate → score/boost → rerank if applicable
```

Recommended scoring:

```text
final_score = semantic_score + metadata_match_boost + title_path_match_boost
```

The exact score weights may be configurable later.

---

## Document Discovery Semantics

`POST /api/v2/documents/search` must return document-level results.

### Hard mode

Return only documents having at least one chunk matching all metadata filters.

### Soft mode

Return documents matched by any of the following signals:

- metadata match
- title/page title match
- source path or filename match
- semantic content match

All results must be deduplicated by `doc_id`.

Each document result should include match reasons:

```json
{
  "doc_id": "prj_apollo/costs.png",
  "title": "costs.png",
  "match_reasons": [
    "metadata:user_metadata.project",
    "semantic"
  ]
}
```

---

## Metadata Schema APIs

Core must expose available payload fields to support the WebUI filter builder.

### GET `/api/v2/metadata/schema`

Returns filterable fields.

Example:

```json
{
  "fields": [
    {
      "field": "user_metadata.project",
      "type": "string",
      "operators": ["eq", "exists"]
    },
    {
      "field": "chunk_type",
      "type": "string",
      "operators": ["eq", "exists"]
    }
  ]
}
```

### GET `/api/v2/metadata/values?field=user_metadata.project`

Returns known values for a field.

---

## Qdrant Filter Builder

Core must implement a reusable Qdrant payload filter builder supporting:

```text
eq
exists
```

for the first implementation.

Examples:

```json
{
  "field": "user_metadata.project",
  "operator": "eq",
  "value": "apollo"
}
```

maps to:

```json
{
  "key": "user_metadata.project",
  "match": { "value": "apollo" }
}
```

---

## Observability

Core must log:

```text
metadata_filter_mode_received
qdrant_filter_built
hard_filter_applied
soft_metadata_candidates_added
document_search_completed
filtered_rag_completed
```

Each log should include:

- correlation_id if provided
- metadata_filter_mode
- filters
- candidate counts
- final result count
- duration_ms

---

## Non-Goals

This SDD does not include:

- Changing existing payload shape
- Injecting metadata into embedded text
- Implementing WebUI controls
- Implementing Gateway request handling
- Authentication/authorization

---

## Acceptance Criteria

1. Core accepts `metadata_filter_mode=hard` and `metadata_filter_mode=soft`.
2. Hard mode applies Qdrant payload filters as mandatory constraints.
3. Hard mode never returns chunks/documents that do not match filters.
4. Soft mode uses metadata as recall/ranking signal and does not exclude untagged relevant content.
5. Filters can target fields beyond `user_metadata`, including `chunk_type` and `language` where present.
6. `/api/v2/documents/search` returns document-level deduplicated results.
7. `/api/v2/retrieval/query` supports both modes.
8. `/api/v2/metadata/schema` exposes filterable payload fields.
9. `/api/v2/metadata/values` returns known values for a selected field.
10. No metadata is injected into embedded content text.

---

## One-Sentence Summary

Retriva Core gains explicit hard and soft metadata filtering modes for both document discovery and RAG retrieval, while preserving metadata as structured payload rather than embedded text.
