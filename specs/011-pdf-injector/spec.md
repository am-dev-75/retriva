# Feature Spec — 011 PDF Injector

## Goal

Add a new injector that indexes local **PDF files** from a recursively
explored directory root, using a **pluggable PDF extraction backend**.
The default backend uses `pdfplumber` (pure Python, Apache-2.0 compatible).
The injector is a peer of the existing HTML and MediaWiki export
injectors — it does not replace or modify them.

## Background

Retriva supports local static HTML mirrors (`wget`-style) and MediaWiki
native XML exports (`--injector mediawiki_export`). A third ingestion
mode is now required for local PDF document corpora — manuals,
diagnostics reports, archived notes — which must be discovered, parsed
page-by-page, chunked, and indexed through the same retrieval pipeline.

### Input shape (from `docs/pdf-injector-contract.md`)

```
/root/pdf-corpus/
  manuals/
    board_x_manual.pdf
  diagnostics/
    startup_leds.pdf
  archived/
    2021/
      fan_curve_notes.pdf
```

## In scope

- Recursive directory discovery for `*.pdf` files
- Pluggable `PdfExtractor` protocol registered in the capability registry
- Default `pdfplumber`-based backend (pure Python, Apache-2.0 compatible)
- Per-page text extraction and per-page API ingestion
- Document title derivation (PDF metadata → first heading → filename)
- Page-aware chunking: each chunk carries a page number
- Graceful handling of encrypted, image-only, or malformed PDFs
- New ingestion API endpoint (`/api/v1/ingest/pdf`)
- CLI integration via `--injector pdf` flag
- Metadata sufficient for citations: `page_title`, `source_path`,
  `page_number`, `language`

## Out of scope

- OCR as a required dependency (image-only PDFs are skipped with a warning)
- Advanced table reconstruction or layout preservation
- Replacing existing injectors
- UI changes
- Cloud document services

## Functional requirements

### FR1 — Recursive discovery
The system shall recursively explore the supplied root directory and
detect candidate `*.pdf` files.

### FR2 — Pluggable PDF extraction
The system shall define a `PdfExtractor` protocol in `protocols.py` and
register the default implementation via the capability registry. Future
backends (e.g., `pymupdf`, `pypdf`) can be swapped by registering a
higher-priority implementation.

### FR3 — Default pdfplumber backend
The default `PdfExtractor` implementation shall use `pdfplumber` to
extract embedded text from each PDF page via `page.extract_text()`.
Pages with no extractable text are skipped with a debug log entry.

### FR4 — Per-page ingestion
Each PDF page is POSTed as a separate ingestion request. This preserves
page-level granularity in citations (e.g., `"Page 42"`).

### FR5 — Document title derivation
The system shall derive a document title with the following priority:
1. PDF metadata `Title` field (if non-empty)
2. First heading-like line from page 1 text
3. Filename stem as fallback

### FR6 — Page-aware metadata
Each emitted chunk shall carry:
- `page_number` — the 1-indexed page from which the chunk text originates
- `section_path` — set to `"Page {N}"` for citation rendering

### FR7 — Graceful failure handling
Encrypted, password-protected, or completely image-only PDFs shall be
skipped with a warning log. They shall not crash the ingestion pipeline.
Partially extractable PDFs (some pages have text, some are images) shall
index only the text-bearing pages.

### FR8 — CLI support
The CLI `ingest` and `reindex` commands shall accept `--injector pdf`.
When set, the CLI discovers `*.pdf` files, parses them, and POSTs each
page to `/api/v1/ingest/pdf`. Default behavior (no flag) is unchanged.

### FR9 — Citation/debug metadata
Every emitted chunk shall carry:
- `doc_id` — `{pdf_filename}#p{page_number}`
- `source_path` — absolute path to the PDF file
- `page_title` — derived document title
- `page_number` — 1-indexed page number
- `chunk_type` — `"text"`

## New dependency

- `pdfplumber>=0.11.0` (pure Python, built on `pdfminer.six`; MIT license).
  Chosen for Apache-2.0 license compatibility and precise text extraction.
  Alternative backends (e.g., `pymupdf`) can be swapped via the registry
  without code changes.

## Acceptance summary

The feature is accepted when a user can run:
```
python -m retriva.cli ingest --path /data/pdf-corpus --injector pdf
```
and have PDF pages parsed per-page, plain text chunked with page-aware
metadata, and all content indexed — without breaking existing ingestion
modes.
