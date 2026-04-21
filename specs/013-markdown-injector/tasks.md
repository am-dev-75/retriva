# Tasks — Markdown Injector

## Phase 1: Infrastructure & Discovery
- [x] Add `.md` and `.markdown` to `FILE_TYPE_REGISTRY` in `src/retriva/ingestion/discover.py`.
- [x] Add `markdown` to `--injector` choices in `src/retriva/cli.py`.
- [x] Implement `run_markdown_ingest` skeleton in `src/retriva/cli.py`.

## Phase 2: Markdown Parsing
- [x] Create `src/retriva/ingestion/markdown_parser.py`.
- [x] Implement logic to extract title (first H1 or filename).
- [x] Implement section splitting based on `#` headings.
- [x] Add unit tests for `MarkdownParser` with various edge cases (nested headings, code fences).

## Phase 3: Backend API Integration
- [x] Define `MarkdownIngestRequest` model in `src/retriva/ingestion_api/schemas.py`.
- [x] Add `/api/v1/ingest/markdown` endpoint to `src/retriva/ingestion_api/main.py`.
- [x] Implement backend handler to process sections into `ParsedDocument` and then to chunks.

## Phase 4: CLI Completion & Testing
- [x] Complete `run_markdown_ingest` in `cli.py` to call the parser and POST to the new endpoint.
- [x] Add integration test: ingest a sample Markdown directory and verify retrieval.
- [x] Verify backward compatibility by running existing `html` and `pdf` ingestion tests.

## Phase 5: Documentation
- [x] Finalize `docs/markdown-injector-contract.md`.
- [x] Add Markdown injection examples to help text or internal docs.
