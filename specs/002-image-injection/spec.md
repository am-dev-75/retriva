# Feature Spec — 002 Image Injection

## Goal

Extend the existing HTML ingestion pipeline to support **image injection**.

Images should be injected using the same conceptual flow as HTML:
- discovery
- normalization
- chunk creation
- indexing

## In scope

- detect images during backend HTML ingestion (server-side parsing)
- resolve local image paths from the HTML `src` fields
- extract basic metadata (alt text, caption, surrounding section) and use it as the chunk's text content
- create image-derived chunks (e.g., `chunk_type="image"`) with an `image_path` field in `ChunkMetadata`
- index image chunks alongside HTML chunks into Qdrant

## Out of scope

- OCR (Optical Character Recognition)
- VLM (Vision Language Models)
- multimodal embeddings (images themselves are not embedded; their metadata text is embedded using standard text models)
- retrieval changes
- creating a separate standalone REST endpoint for raw binary image ingestion (images must be ingested as part of HTML contexts)

## Acceptance summary

The system can ingest images seamlessly without breaking HTML ingestion, and image-derived chunks appear in the index with their inferred textual contexts.
