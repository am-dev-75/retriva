# Tasks — True Cross-Language Retrieval

## Phase 1: Ingestion & Metadata Tracking
- [ ] Add `language` attribute to Pydantic objects inside `src/retriva/ingestion_api/schemas.py`.
- [ ] Extract `lang` attribute from document root HTML instances inside `src/retriva/ingestion/html_parser.py`.
- [ ] Modify `src/retriva/ingestion_api/routers/ingest_HTML.py` to route `language` into memory. 
- [ ] (Optional) Provide heuristic/CLI language fallback support for `/ingest/image` and `/ingest/text`.

## Phase 2: Qdrant Shared Space Layer
- [ ] Implement robust `chunk.language` metadata persistence across upsert blocks in `src/retriva/indexing/qdrant_store.py`.
- [ ] Re-ingest the corpus locally to ensure legacy structures are not compromised and metadata applies seamlessly.

## Phase 3: QA Generation & Prompt Interception
- [ ] Implement explicit language agreement enforcement instructions within the `build_prompt()` function located at `src/retriva/qa/prompting.py`.
- [ ] Verify contextual data blocks correctly surface `language` metadata through QA functions.

## Phase 4: UI & Citation Preservation
- [ ] Expand definitions in `src/retriva/openai_api/schemas.py` to surface `language` alongside Citation structures natively.
- [ ] Design and test Streamslit frontend modifications inside `src/retriva/ui/streamlit_app.py` for cleanly displaying source metadata language origin markers embedded next to chunk titles or URLs.
