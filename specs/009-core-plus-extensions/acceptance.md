# Acceptance Criteria — 009 Core + Proprietary Extensions

## Zero-extension mode
- All existing OSS functionality works unchanged when `RETRIVA_EXTENSIONS`
  is unset or empty.
- Existing tests (OpenAI API, ingestion API, bilingual benchmark, job
  manager) pass without modification.

## Extension override
- A test extension module can register a mock `Retriever` at priority 200.
- When loaded, the mock retriever is selected over `DefaultRetriever`.
- The chat completions endpoint uses the mock retriever for context.

## Isolation
- `grep -r "import.*proprietary\|import.*extension" src/retriva/` returns
  zero hits — the core never imports extension code directly.
- Extensions are discovered only through `RETRIVA_EXTENSIONS` and
  `importlib.import_module`.

## Invariants preserved
- Public API routes (`/v1/chat/completions`, `/api/v1/ingest/*`,
  `/api/v1/jobs/*`) have identical request/response schemas.
- Citation format, grounding validation, and language alignment are
  unchanged.

## Multiple extensions
- Two independent extension modules can be loaded simultaneously.
- Each registers implementations for different capabilities without conflict.
