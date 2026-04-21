# Implementation Plan — Markdown Injector

## Phase 1 — Discovery and CLI Wiring
- Add `.md` and `.markdown` to the `FILE_TYPE_REGISTRY`.
- Wire up the `--injector markdown` flag in the CLI.
- Establish the `run_markdown_ingest` loop.

## Phase 2 — Local Markdown Parser
- Implement a section-aware parser that preserves heading hierarchy.
- Ensure document title is correctly derived from content or path.
- Add unit tests for structural preservation.

## Phase 3 — Backend API Support
- Add a new ingestion endpoint `/api/v1/ingest/markdown`.
- Map the structured Markdown payload to internal `ParsedDocument` objects.
- Ensure the existing chunking pipeline receives the section-aware data.

## Phase 4 — End-to-End Validation
- Run integration tests with a mock Markdown corpus.
- Verify citations show correct document titles and section paths.
- Perform regression testing on HTML and PDF pipelines.

## Phase 5 — Final Polish
- Refine error handling for malformed Markdown.
- Update documentation and help strings.
