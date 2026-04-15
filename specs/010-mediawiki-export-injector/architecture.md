# Architecture — 010 MediaWiki Native Export Injector

## Layered view

```
┌──────────────────────────────────────────────────────────────┐
│  CLI (cli.py)                                                │
│  --injector mediawiki_export  → run_mediawiki_ingest()       │
│  (no flag)                    → run_ingest() [unchanged]     │
├──────────────────────────────────────────────────────────────┤
│  Ingestion API                                               │
│  POST /api/v1/ingest/mediawiki  [NEW]                        │
│  POST /api/v1/ingest/html       [unchanged]                  │
├──────────────────────────────────────────────────────────────┤
│  MediaWiki Export Parser  [NEW]                              │
│  src/retriva/ingestion/mediawiki_export_parser.py            │
│  ── iterparse XML → WikiPage objects                         │
│  ── wikitext → plain text                                    │
│  ── [[File:…]] reference extraction                          │
├──────────────────────────────────────────────────────────────┤
│  Asset Resolver  [NEW]                                       │
│  src/retriva/ingestion/mediawiki_assets.py                   │
│  ── build index of assets/ subtree                           │
│  ── resolve file references → local paths                    │
├──────────────────────────────────────────────────────────────┤
│  Existing shared pipeline                                    │
│  Chunker ← registry    Embeddings    Qdrant upsert           │
│  VLM Describer ← registry (for resolved images)              │
└──────────────────────────────────────────────────────────────┘
```

## New modules

### `src/retriva/ingestion/mediawiki_export_parser.py`

Streaming XML parser using `xml.etree.ElementTree.iterparse`.

```python
@dataclass
class WikiPage:
    title: str
    namespace: int
    page_id: int
    text: str             # raw wikitext
    timestamp: str
    file_references: list[str]  # extracted [[File:…]] names

def parse_export(xml_path: Path) -> Iterator[WikiPage]:
    """Yield WikiPage objects from a MediaWiki XML export file."""
    ...

def wikitext_to_plaintext(wikitext: str) -> str:
    """Strip MediaWiki markup, returning clean text for chunking."""
    ...

def extract_file_references(wikitext: str) -> list[str]:
    """Return filenames from [[File:…]] and [[Image:…]] links."""
    ...
```

### `src/retriva/ingestion/mediawiki_assets.py`

Asset index and resolver.

```python
def build_asset_index(assets_dir: Path) -> dict[str, Path]:
    """Recursively scan assets/ and return {lowercase_name: path}."""
    ...

def resolve_file_reference(name: str, index: dict[str, Path]) -> Path | None:
    """Case-insensitive lookup of a file reference against the index."""
    ...
```

### `src/retriva/ingestion_api/routers/ingest_mediawiki.py`

New API endpoint following the same pattern as `ingest_text.py`:

```python
class MediaWikiIngestRequest(BaseModel):
    source_path: str          # path to XML file
    page_title: str
    content_text: str         # plaintext extracted from wikitext
    page_id: int
    namespace: int = 0
    linked_assets: list[str] = []  # resolved asset paths

@router.post("/mediawiki", ...)
async def ingest_mediawiki(payload, background_tasks):
    ...
```

## CLI evolution

```
python -m retriva.cli ingest --path /data/wiki-export --injector mediawiki_export
```

- When `--injector mediawiki_export` is set, the CLI calls
  `run_mediawiki_ingest()` instead of `run_ingest()`.
- `run_mediawiki_ingest()` discovers XML files, parses them, resolves
  assets, and POSTs each page to `/api/v1/ingest/mediawiki`.
- When `--injector` is omitted, existing behavior is unchanged.

## Discovery strategy

The MediaWiki injector has its own discovery logic (not merged into
`discover.py`'s `FILE_TYPE_REGISTRY`), because the input shape is
fundamentally different:

1. Walk the root directory for `*.xml` files.
2. Validate each by sniffing the first 1 KB for `<mediawiki`.
3. Find `assets/` directories at or below the root.
4. Build the asset index from the `assets/` subtree.

## Data flow per page

```
XML file → iterparse → WikiPage
  → wikitext_to_plaintext() → content_text
  → extract_file_references() → resolve against asset index
  → POST /api/v1/ingest/mediawiki
    → ParsedDocument → chunker (via registry) → embeddings → Qdrant
    → resolved images → VLM describer (via registry) → image chunks
```

## Dependency rule

- The new modules import from `retriva.domain.models`,
  `retriva.registry`, `retriva.logger` — all existing core.
- The HTML injector is **not** modified.
- The new modules use **no new external dependencies** (stdlib
  `xml.etree.ElementTree` and `re` only).
