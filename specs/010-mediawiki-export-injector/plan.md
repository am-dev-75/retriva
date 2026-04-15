# Implementation Plan — 010 MediaWiki Native Export Injector

## Phase 1 — XML Parser

1. Create `src/retriva/ingestion/mediawiki_export_parser.py`:
   - `WikiPage` dataclass (`title`, `namespace`, `page_id`, `text`,
     `timestamp`, `file_references`)
   - `parse_export(xml_path)` — streaming iterparse of `<page>` elements,
     yields `WikiPage` objects, only keeps latest revision
   - `wikitext_to_plaintext(wikitext)` — regex-based stripping:
     `== headings ==` → headings, `'''bold'''` → plain,
     `[[Link|Label]]` → Label, `{{templates}}` → removed,
     `<ref>…</ref>` → removed, HTML tags → removed
   - `extract_file_references(wikitext)` — regex for
     `[[File:name.ext…]]` and `[[Image:name.ext…]]`
   - `is_mediawiki_export(xml_path)` — sniff first 1 KB for `<mediawiki`

2. Add unit tests: `tests/test_mediawiki_parser.py`
   - Parse a small fixture XML with 2–3 pages
   - Validate wikitext stripping edge cases
   - Validate file reference extraction

## Phase 2 — Asset Resolver

1. Create `src/retriva/ingestion/mediawiki_assets.py`:
   - `build_asset_index(assets_dir)` — recursive walk, returns
     `{lowercase_stem_or_name: Path}`
   - `resolve_file_reference(name, index)` — case-insensitive match

2. Add unit tests: `tests/test_mediawiki_assets.py`
   - Build index from a temporary directory with known files
   - Resolve with exact match, case mismatch, missing file

## Phase 3 — Ingestion API Endpoint

1. Add `MediaWikiIngestRequest` to `src/retriva/ingestion_api/schemas.py`
2. Create `src/retriva/ingestion_api/routers/ingest_mediawiki.py`:
   - `POST /api/v1/ingest/mediawiki`
   - Background worker: build `ParsedDocument`, chunk via registry,
     VLM-enrich resolved images via registry, upsert to Qdrant
3. Register the router in `src/retriva/ingestion_api/main.py`

## Phase 4 — CLI Integration

1. Add `--injector` argument to `ingest` and `reindex` subcommands in
   `src/retriva/cli.py`
2. Implement `run_mediawiki_ingest(target, api_url, limit)`:
   - Walk `target` for `*.xml` files validated by `is_mediawiki_export()`
   - Find `assets/` directories, build asset index
   - For each XML: `parse_export()` → for each `WikiPage`:
     - `wikitext_to_plaintext()` → POST to `/api/v1/ingest/mediawiki`
   - For resolved image assets: POST to `/api/v1/ingest/image`
3. Default CLI behavior (no `--injector` flag) remains unchanged

## Phase 5 — Verification

1. **Fixture test** (`tests/test_mediawiki_injector.py`):
   - Create a small XML fixture (3 pages with `[[File:…]]` refs)
   - Create a mock `assets/` directory with matching files
   - Verify end-to-end: discovery → parsing → asset resolution → API call
2. **Regression**: all existing tests pass (HTML ingestion, OpenAI API,
   registry, bilingual benchmark)
3. **Manual**: run against a real MediaWiki export mirror
