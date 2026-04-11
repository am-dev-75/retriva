# Architecture — Image Injection

## Design principle

Image injection must act as a seamless extension of the HTML ingestion pipeline, extracting value without imposing architectural drift on the Modular Injection API.

## Proposed components

- **ImageParser**: Evaluates the raw HTML DOM within the backend API to yield `ImageContext` items (src, alt text, parental context) before boilerplate tags are stripped out.
- **ImageChunker**: Converts `ImageContext` metadata into standard `Chunk` models natively tailored for dense retrieval.

These should align internally with existing HTML ingestion functions inside `src/retriva/ingestion/`.

## ingest.py changes

Raw HTML sent to `/api/v1/ingest/html` will natively route to both text extraction and image extraction simultaneously. 
There is **no need** for a standalone `ingest_images()` entrypoint since the system does not support VLM processing and therefore relies universally on the surrounding HTML context to index images. The ingestion entrypoint remains unified.
