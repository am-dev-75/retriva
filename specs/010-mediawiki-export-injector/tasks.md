# Tasks — 010 MediaWiki Native Export Injector

## Phase 1: XML Parser
- [ ] Create `src/retriva/ingestion/mediawiki_export_parser.py`
- [ ] Implement `WikiPage` dataclass
- [ ] Implement `parse_export()` with iterparse
- [ ] Implement `wikitext_to_plaintext()` with regex stripping
- [ ] Implement `extract_file_references()` for `[[File:…]]` / `[[Image:…]]`
- [ ] Implement `is_mediawiki_export()` sniffing function
- [ ] Add `tests/test_mediawiki_parser.py` with XML fixture

## Phase 2: Asset Resolver
- [ ] Create `src/retriva/ingestion/mediawiki_assets.py`
- [ ] Implement `build_asset_index()` recursive scan
- [ ] Implement `resolve_file_reference()` case-insensitive lookup
- [ ] Add `tests/test_mediawiki_assets.py`

## Phase 3: Ingestion API Endpoint
- [ ] Add `MediaWikiIngestRequest` to `ingestion_api/schemas.py`
- [ ] Create `ingestion_api/routers/ingest_mediawiki.py`
- [ ] Register router in `ingestion_api/main.py`

## Phase 4: CLI Integration
- [ ] Add `--injector` argument to `ingest` and `reindex` subcommands
- [ ] Implement `run_mediawiki_ingest()` in `cli.py`
- [ ] Wire up discovery → parsing → asset resolution → API calls

## Phase 5: Verification
- [ ] End-to-end fixture test with XML + assets
- [ ] Regression: all existing tests pass unchanged
- [ ] Manual verification against a real export mirror
