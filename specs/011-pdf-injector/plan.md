# Implementation Plan — 011 PDF Injector

## Phase 1 — PDF Parser + Protocol

1. Add `pdfplumber>=0.11.0` to `requirements.txt`
2. Add `PdfExtractor` protocol to `src/retriva/protocols.py`:
   - `extract_pages(pdf_path) -> list[PdfPage] | None`
   - `extract_metadata(pdf_path) -> dict[str, str]`
3. Create `src/retriva/ingestion/pdf_parser.py`:
   - `PdfPage` dataclass (`page_number`, `text`)
   - `PdfDocument` dataclass (`title`, `source_path`, `pages`,
     `total_pages`, `skipped_pages`)
   - `PdfPlumberExtractor` class implementing `PdfExtractor`:
     - `extract_pages()` — `pdfplumber.open()`, iterate pages,
       `page.extract_text()`, skip empty pages
     - `extract_metadata()` — return `pdf.metadata` dict
     - Registered at priority 100 via `CapabilityRegistry`
   - `parse_pdf(pdf_path)` — resolves `PdfExtractor` from registry,
     calls `extract_pages()` + `extract_metadata()`, builds `PdfDocument`
   - `derive_title(metadata, first_page_text, pdf_path)` — PDF metadata
     `Title` → first heading-like line → filename stem
4. Add unit tests: `tests/test_pdf_parser.py`
   - Create PDF fixture programmatically with `pdfplumber`'s test utils
     or a minimal PDF binary
   - Verify page text, page numbers, title derivation
   - Verify encrypted PDF returns None gracefully
   - Verify empty pages are skipped

## Phase 2 — Ingestion API Endpoint

1. Add `PdfIngestRequest` to `src/retriva/ingestion_api/schemas.py`
2. Create `src/retriva/ingestion_api/routers/ingest_pdf.py`:
   - `POST /api/v1/ingest/pdf`
   - Background worker: build `ParsedDocument` with
     `section_path="Page {N}"`, chunk via registry, upsert to Qdrant
3. Register the router in `src/retriva/ingestion_api/main.py`

## Phase 3 — CLI Integration

1. Add `"pdf"` to the `--injector` choices list in `cli.py`
2. Implement `run_pdf_ingest(target, api_url, limit)`:
   - Walk `target` for `*.pdf` files
   - For each PDF: `parse_pdf()` → for each `PdfPage`:
     - POST to `/api/v1/ingest/pdf`
3. Default CLI behavior (no `--injector` flag) remains unchanged

## Phase 4 — Verification

1. **Parser tests** (`tests/test_pdf_parser.py`):
   - Page extraction, title derivation, encrypted handling
2. **API + integration tests** (`tests/test_pdf_injector.py`):
   - Endpoint accepts valid payloads (202 response)
   - End-to-end: fixture PDF → parse → API → chunks
3. **Regression**: all existing 91+ tests pass unchanged
