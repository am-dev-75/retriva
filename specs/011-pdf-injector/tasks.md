# Tasks — 011 PDF Injector

## Phase 1: PDF Parser + Protocol
- [ ] Add `pdfplumber>=0.11.0` to `requirements.txt`
- [ ] Add `PdfExtractor` protocol to `protocols.py`
- [ ] Create `src/retriva/ingestion/pdf_parser.py`
- [ ] Implement `PdfPage` and `PdfDocument` dataclasses
- [ ] Implement `PdfPlumberExtractor` (default backend, priority 100)
- [ ] Implement `parse_pdf()` using registry-resolved extractor
- [ ] Implement `derive_title()` (metadata → heading → filename)
- [ ] Handle encrypted / image-only PDFs gracefully
- [ ] Add `tests/test_pdf_parser.py` with programmatic PDF fixture

## Phase 2: Ingestion API Endpoint
- [ ] Add `PdfIngestRequest` to `ingestion_api/schemas.py`
- [ ] Create `ingestion_api/routers/ingest_pdf.py`
- [ ] Register router in `ingestion_api/main.py`

## Phase 3: CLI Integration
- [ ] Add `"pdf"` to `--injector` choices in `cli.py`
- [ ] Implement `run_pdf_ingest()` in `cli.py`
- [ ] Wire up discovery → parsing → per-page API calls

## Phase 4: Verification
- [ ] Parser unit tests with programmatic PDF fixture
- [ ] API endpoint acceptance test
- [ ] End-to-end fixture test
- [ ] Regression: all existing tests pass unchanged
