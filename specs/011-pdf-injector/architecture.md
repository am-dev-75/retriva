# Architecture — 011 PDF Injector

## Layered view

```
┌──────────────────────────────────────────────────────────────┐
│  CLI (cli.py)                                                │
│  --injector pdf              → run_pdf_ingest()              │
│  --injector mediawiki_export → run_mediawiki_ingest()        │
│  (no flag)                   → run_ingest() [unchanged]      │
├──────────────────────────────────────────────────────────────┤
│  Ingestion API                                               │
│  POST /api/v1/ingest/pdf        [NEW]                        │
│  POST /api/v1/ingest/mediawiki  [unchanged]                  │
│  POST /api/v1/ingest/html       [unchanged]                  │
├──────────────────────────────────────────────────────────────┤
│  PdfExtractor protocol  [NEW — in protocols.py]              │
│  ── registered in CapabilityRegistry as "pdf_extractor"      │
│  ── default: PdfPlumberExtractor (priority 100)              │
│  ── future:  PyMuPdfExtractor   (priority 200, extension)    │
├──────────────────────────────────────────────────────────────┤
│  PDF Parser  [NEW]                                           │
│  src/retriva/ingestion/pdf_parser.py                         │
│  ── PdfPlumberExtractor (default implementation)             │
│  ── PdfPage / PdfDocument dataclasses                        │
│  ── derive_title() logic                                     │
│  ── error handling for encrypted / image-only                │
├──────────────────────────────────────────────────────────────┤
│  Existing shared pipeline                                    │
│  Chunker ← registry    Embeddings    Qdrant upsert           │
└──────────────────────────────────────────────────────────────┘
```

## Protocol definition (in `protocols.py`)

```python
@runtime_checkable
class PdfExtractor(Protocol):
    """Extract text page-by-page from a PDF file."""

    def extract_pages(self, pdf_path: Path) -> list[PdfPage] | None:
        """
        Return a list of PdfPage objects with extracted text, or
        None if the PDF is unreadable (encrypted, corrupt).
        """
        ...

    def extract_metadata(self, pdf_path: Path) -> dict[str, str]:
        """Return PDF metadata (title, author, etc.) as a dict."""
        ...
```

## New modules

### `src/retriva/ingestion/pdf_parser.py`

Default `pdfplumber`-based implementation + dataclasses + title derivation.

```python
@dataclass
class PdfPage:
    page_number: int        # 1-indexed
    text: str               # extracted text for this page

@dataclass
class PdfDocument:
    title: str              # derived title
    source_path: str        # absolute path to the PDF
    pages: list[PdfPage]    # non-empty pages only
    total_pages: int        # total pages in the PDF
    skipped_pages: int      # pages with no extractable text

class PdfPlumberExtractor:
    """Default PdfExtractor using pdfplumber (pure Python)."""

    def extract_pages(self, pdf_path: Path) -> list[PdfPage] | None: ...
    def extract_metadata(self, pdf_path: Path) -> dict[str, str]: ...

# Registered at priority 100 via CapabilityRegistry

def parse_pdf(pdf_path: Path) -> PdfDocument | None:
    """
    High-level function that uses the registry-resolved PdfExtractor
    to parse a PDF into a PdfDocument.
    """
    ...

def derive_title(metadata: dict[str, str], first_page_text: str,
                 pdf_path: Path) -> str:
    """
    Derive document title:
    1. PDF metadata 'Title' field
    2. First heading-like line from page 1
    3. Filename stem
    """
    ...
```

### `src/retriva/ingestion_api/routers/ingest_pdf.py`

New API endpoint `POST /api/v1/ingest/pdf`:

```python
class PdfIngestRequest(BaseModel):
    source_path: str          # path to PDF file
    page_title: str           # derived document title
    content_text: str         # plaintext for one page
    page_number: int          # 1-indexed
    total_pages: int          # total pages in the document
```

## CLI evolution

```
python -m retriva.cli ingest --path /data/pdf-corpus --injector pdf
```

- The `--injector` choices list grows from `["mediawiki_export"]` to
  `["mediawiki_export", "pdf"]`.
- `run_pdf_ingest()` discovers `*.pdf` files, resolves the
  `PdfExtractor` from the registry, parses each PDF, and POSTs
  **one request per page** to `/api/v1/ingest/pdf`.

## Data flow per page

```
PDF file → PdfExtractor.extract_pages() → list[PdfPage]
  → derive_title() from metadata + page 1
  → for each PdfPage:
    → POST /api/v1/ingest/pdf
      → ParsedDocument (section_path="Page {N}")
        → chunker (via registry) → embeddings → Qdrant
```

## Dependency rule

- The new module imports `pdfplumber` — the only new external dependency.
- Existing injectors are **not** modified.
- `requirements.txt` is updated to include `pdfplumber>=0.11.0`.
- Future backends (e.g., `pymupdf`) can be added as extensions
  registering at priority > 100 — zero code changes to core.
