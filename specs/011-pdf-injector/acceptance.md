# Acceptance Criteria — 011 PDF Injector

## Core functionality
- A user can run `python -m retriva.cli ingest --path /data/pdfs
  --injector pdf` and have PDF pages indexed.
- `*.pdf` files are discovered recursively from the supplied root.
- Text is extracted page-by-page using the registry-resolved
  `PdfExtractor` (default: `PdfPlumberExtractor`).
- Each page is ingested as a separate API request for page-level
  citation granularity.
- Pages with no extractable text are skipped with a debug log.
- Document titles are derived from PDF metadata, first heading, or
  filename stem.

## Pluggable architecture
- A `PdfExtractor` protocol is defined in `protocols.py`.
- The default `PdfPlumberExtractor` is registered at priority 100.
- A future extension can register an alternative backend (e.g., pymupdf)
  at priority > 100 to override the default — zero core code changes.

## Metadata
- Every emitted chunk carries `doc_id`, `page_title`, `source_path`,
  `page_number`, and `chunk_type`.
- `section_path` is set to `"Page {N}"` for citation rendering in
  Open WebUI.

## Failure handling
- Encrypted PDFs are skipped with a warning log — no crash.
- Image-only PDFs are skipped with a warning log — no crash.
- Partially extractable PDFs index only text-bearing pages.

## Backward compatibility
- Running `ingest` without `--injector` uses the existing HTML/image/text
  pipeline — zero behavior change.
- Existing MediaWiki export, HTML, and OpenAI API tests all pass unchanged.
- The repository root `README.md` is not modified.

## Isolation
- Existing injector code is not modified.
- The only new external dependency is `pdfplumber>=0.11.0` (MIT license).

## Test coverage
- Unit tests for PDF parsing (text extraction, title derivation,
  encrypted handling, empty pages).
- API endpoint acceptance test.
- Integration fixture test: PDF → parse → API → chunks.
