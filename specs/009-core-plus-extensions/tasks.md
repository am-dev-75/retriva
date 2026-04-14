# Tasks — 009 Core + Proprietary Extensions

## Phase 1: Protocols & Registry
- [ ] Create `src/retriva/protocols.py` — Retriever, Chunker, HTMLParser, VLMDescriber, PromptBuilder
- [ ] Create `src/retriva/registry.py` — CapabilityRegistry singleton

## Phase 2: Default implementations
- [ ] Add `DefaultRetriever` class to `qa/retriever.py`, register at priority 100
- [ ] Add `DefaultChunker` class to `ingestion/chunker.py`, register at priority 100
- [ ] Add `DefaultHTMLParser` class to `ingestion/html_parser.py`, register at priority 100
- [ ] Add `DefaultVLMDescriber` class to `ingestion/vlm_describer.py`, register at priority 100
- [ ] Add `DefaultPromptBuilder` class to `qa/prompting.py`, register at priority 100

## Phase 3: Refactor call sites
- [ ] `qa/answerer.py` — resolve retriever and prompt_builder from registry
- [ ] `ingestion_api/routers/ingest_HTML.py` — resolve html_parser and chunker from registry
- [ ] `ingestion_api/routers/ingest_image.py` — resolve vlm_describer from registry
- [ ] `ingestion_api/routers/ingest_text.py` — resolve chunker from registry
- [ ] `ingestion/image_parser.py` — resolve vlm_describer from registry

## Phase 4: Extension discovery
- [ ] Add `retriva_extensions` setting to `config.py`
- [ ] Implement `CapabilityRegistry.load_extensions()` with importlib
- [ ] Call `load_extensions()` in `openai_api/main.py` lifespan
- [ ] Call `load_extensions()` in `ingestion_api/main.py` lifespan

## Phase 5: Verification
- [ ] Unit tests for registry priority resolution and thread safety
- [ ] Integration test with mock extension module
- [ ] Regression: all existing tests pass with no extensions loaded
