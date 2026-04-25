# Architecture — User-Provided Metadata (v1)

## Design principle
Metadata flows with the document through the ingestion pipeline and becomes part
of chunk metadata used by the vector index.

## Data flow

Client → ingestion_api_v1 → Document → Chunks → Index

At each stage, `user_metadata` is preserved and propagated.

## Storage implications
- Document store: persists metadata
- Chunk store / vector index: embeds metadata per chunk

## Non-goals
- No metadata-driven branching
- No injector replacement
