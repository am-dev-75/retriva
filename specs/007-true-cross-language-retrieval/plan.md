# Implementation Plan — True Cross-Language Retrieval

### 1. Data Schema & Ingestion Updates
- **Metadata**: Add `language: Optional[str] = None` to `IngestDocRequest` and `Chunk` schemas inside `schemas.py`.
- **HTML Parser**: In `ingestion/html_parser.py`, extract the `lang` attribute from `<html>` tags. 
- **Endpoint Routers**: Update `ingestion_api/routers/ingest_HTML.py` and `ingest_text.py` to securely store detected language parameters into the objects mapped out to Qdrant.

### 2. Qdrant Store Alignment
- **Payload Mod**: Update `upsert_chunks()` within `indexing/qdrant_store.py` to insert `chunk.language` into Qdrant's serialized payload matrix. Verify any backward compatibility issues with previously indexed items by using `.get("language", "unknown")`.

### 3. Streamlit End-User UI
- **Citation Badges**: In `ui/streamlit_app.py`, update `View Retrieval Context & Citations` visual elements. Attach a clear language tag metadata badge near the canonical URL text.

### 4. Language-Match Prompting Update
- **QA Modification**: In `qa/prompting.py`, rewrite the `build_prompt` method's system prompt payload. Insert a core contextual constraint directly demanding output language strictly matches query language regardless of context origins.

### 5. OpenAI API Compat Metadata
- **OpenAI Endpoint Mods**: Push upstream chunk `language` info into the `MessageMetadata` citation structures stored in `openai_api/schemas.py`. Ensure Open WebUI receives citation language tracking transparently.
